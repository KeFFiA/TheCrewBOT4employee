import re

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from API_SCRIPTS.iiko_cloudAPI import create_update_customer
from Bot import dialogs
from Bot.Keyboards.inline_keyboards import create_menu_keyboard, create_register_menu, choose_sex_menu, \
    privacy_keyboard, create_user_menu_me, create_user_menu_card
from Bot.Keyboards.keyboards import send_contact
from Bot.Utils.states import Register
from Database.database import db
from Scripts.scripts import generate_qr_card, find_referrer_name

user_router = Router()


# COMMANDS/MESSAGES

@user_router.message(CommandStart())
async def start_cmd(message: Message, bot: Bot, state: FSMContext, command: CommandObject):
    user_check = db.query(query="SELECT is_registered FROM users WHERE user_id=%s", values=(message.from_user.id,),
                          fetch='fetchone')[0]
    if user_check:
        await message.answer(text=dialogs.RU_ru['navigation']['menu'],
                             reply_markup=await create_menu_keyboard(message.from_user.id))
        await state.clear()
    else:
        db.query(
            query="INSERT INTO users (user_id, username, user_name, user_surname) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            values=(
                message.from_user.id, message.from_user.username, message.from_user.first_name,
                message.from_user.last_name),
            log_level=10,
            msg=f'User {message.from_user.id} already exist')

        if command.args:
            referrer_user_id = command.args
            referrer_id = db.query(query='SELECT guest_id FROM customers WHERE user_id=%s', values=(referrer_user_id,),
                                   fetch='fetchone')
            referer_name = await find_referrer_name(referrer_id)
        else:
            referrer_id = None
            referer_name = dialogs.RU_ru['empty']

        db.query(query='INSERT INTO customers (user_id, referrer_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
                 values=(message.from_user.id, referrer_id))
        result = db.query(query="""SELECT name, middlename, surname, birthday, sex, phone, email
                                   FROM customers WHERE user_id=%s""", values=(message.from_user.id,), fetch='fetchone')

        if result:
            sex_list = [dialogs.RU_ru['navigation']['not_match'], dialogs.RU_ru['navigation']['male'],
                        dialogs.RU_ru['navigation']['female']]
            name, middlename, surname, birthday, sex, phone, email = (
                value if value is not None else dialogs.RU_ru['empty'] for value in result
            )
            promo = db.query("SELECT receive_promo FROM customers WHERE user_id=%s",
                             values=(message.from_user.id,), fetch='fetchone')[0]

            if promo == 'true':
                _promo = '✅'
            else:
                _promo = '❌'

            await message.answer(text=dialogs.RU_ru['register']['start'].format(us_name=message.from_user.first_name,
                                                                                name=name, birthday=birthday,
                                                                                sex=sex_list[0],
                                                                                referrer=referer_name,
                                                                                phone=phone, email=email, promo=_promo),
                                 reply_markup=await create_register_menu())


@user_router.message(Command('menu'))
async def menu_cmd(message: Message, state: FSMContext):
    await message.answer(text=dialogs.RU_ru['navigation']['menu'],
                         reply_markup=await create_menu_keyboard(message.from_user.id)
                         )
    await state.clear()


@user_router.message(F.contact)
async def register_contact(message: Message, bot: Bot):
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        db.query(query="UPDATE customers SET phone=%s WHERE user_id = %s",
                 values=(message.contact.phone_number, message.from_user.id))
    except:
        pass
    result = db.query(query="""SELECT name, middlename, surname, birthday, sex, phone, email, referrer_id
                                                       FROM customers WHERE user_id=%s""",
                      values=(message.from_user.id,),
                      fetch='fetchone')
    if result:
        sex_list = [dialogs.RU_ru['navigation']['not_match'], dialogs.RU_ru['navigation']['male'],
                    dialogs.RU_ru['navigation']['female']]

        name, middlename, surname, birthday, sex, phone, email, referrer_id = (
            value if value is not None else dialogs.RU_ru['empty'] for value in result
        )
        promo = db.query("SELECT receive_promo FROM customers WHERE user_id=%s",
                         values=(message.from_user.id,), fetch='fetchone')[0]

        if promo == 'true':
            _promo = '✅'
        else:
            _promo = '❌'

        if referrer_id is not None:
            referrer_name = await find_referrer_name(referrer_id)
        else:
            referrer_name = dialogs.RU_ru['empty']

        if middlename is not None:
            _name = f'{surname} {name} {middlename}'
        else:
            _name = f'{surname} {name}'

        try:
            _sex = sex_list[int(sex)]
        except:
            _sex = sex_list[0]

        await message.answer(text=dialogs.RU_ru['register']['start'].format(us_name=message.from_user.first_name,
                                                                            name=_name, birthday=birthday,
                                                                            sex=_sex,
                                                                            referrer=referrer_name,
                                                                            phone=phone, email=email, promo=_promo),
                             reply_markup=await create_register_menu())


@user_router.message(Register.step)
async def register_step(message: Message, state: FSMContext):
    date_pattern = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
    text = message.text.strip()

    if message.entities:
        email = [entity for entity in message.entities if entity.type == 'email']
        if email:
            _email = email[0].extract_from(message.text)
            db.query(query="UPDATE customers SET email=%s WHERE user_id=%s", values=(_email, message.from_user.id))
    elif date_pattern.match(text):
        birthday = text
        db.query(query="UPDATE customers SET birthday=%s WHERE user_id=%s", values=(birthday, message.from_user.id))
    else:
        text = text.split(" ", maxsplit=3)
        if len(text) == 3:
            surname = text[0]
            name = text[1]
            middlename = text[2]
        else:
            surname = text[0]
            name = text[1]
            middlename = None
        db.query(query="UPDATE customers SET name=%s, surname=%s, middlename=%s WHERE user_id=%s",
                 values=(name, surname, middlename, message.from_user.id))

    result = db.query(query="""SELECT name, middlename, surname, birthday, sex, phone, email, referrer_id
                                                   FROM customers WHERE user_id=%s""", values=(message.from_user.id,),
                      fetch='fetchone')
    if result:
        sex_list = [dialogs.RU_ru['navigation']['not_match'], dialogs.RU_ru['navigation']['male'],
                    dialogs.RU_ru['navigation']['female']]

        name, middlename, surname, birthday, sex, phone, email, referrer_id = (
            value if value is not None else dialogs.RU_ru['empty'] for value in result
        )
        promo = db.query("SELECT receive_promo FROM customers WHERE user_id=%s",
                         values=(message.from_user.id,), fetch='fetchone')[0]

        if promo == 'true':
            _promo = '✅'
        else:
            _promo = '❌'

        if referrer_id is not None:
            referrer_name = await find_referrer_name(referrer_id)
        else:
            referrer_name = dialogs.RU_ru['empty']

        if middlename is not None:
            _name = f'{surname} {name} {middlename}'
        else:
            _name = f'{surname} {name}'

        try:
            _sex = sex_list[int(sex)]
        except:
            _sex = sex_list[0]

        await message.answer(text=dialogs.RU_ru['register']['start'].format(us_name=message.from_user.first_name,
                                                                            name=_name, birthday=birthday,
                                                                            sex=_sex,
                                                                            referrer=referrer_name,
                                                                            phone=phone, email=email, promo=_promo),
                             reply_markup=await create_register_menu())

    await state.clear()


# CALLBACKS


@user_router.callback_query(F.data == 'main_menu')
async def main_menu_call(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.edit_text(text=dialogs.RU_ru['navigation']['menu'],
                                     reply_markup=await create_menu_keyboard(call.from_user.id)
                                     )
    except:
        await call.message.delete()
        await call.message.answer(text=dialogs.RU_ru['navigation']['menu'],
                                  reply_markup=await create_menu_keyboard(call.from_user.id)
                                  )


@user_router.callback_query(F.data.startswith('iiko_'))
async def iiko_menu(call: CallbackQuery):
    data = call.data.removeprefix('iiko_')

    result = db.query(query="""SELECT name, middlename, surname, birthday, sex, phone, email, referrer_id, card_number, category
                                                               FROM customers WHERE user_id=%s""",
                      values=(call.from_user.id,),
                      fetch='fetchone')
    if result:
        sex_list = [dialogs.RU_ru['navigation']['not_match'], dialogs.RU_ru['navigation']['male'],
                    dialogs.RU_ru['navigation']['female']]
        name, middlename, surname, birthday, sex, phone, email, referrer_id, card_number, category = (
            value if value is not None else dialogs.RU_ru['empty'] for value in result
        )

        if middlename is not None:
            _name = f'{surname} {name} {middlename}'
        else:
            _name = f'{surname} {name}'

        if referrer_id is not None:
            referrer_name = await find_referrer_name(referrer_id)
        else:
            referrer_name = dialogs.RU_ru['empty']

        try:
            _sex = sex_list[int(sex)]
        except:
            _sex = sex_list[0]

        if data == 'me':
            await call.message.delete()
            url = f'https://t.me/TheCrewEnergyBot?start={call.from_user.id}'
            await call.message.answer(text=dialogs.RU_ru['user']['info'].format(
                name=_name, phone=phone, email=email, sex=_sex, referrer=referrer_name,
                user_id=call.from_user.id, birthday=birthday, category=category, url=url
            ),
                reply_markup=await create_user_menu_me())
        if data == 'card':
            await call.message.delete()
            qr_image = await generate_qr_card(card_number=card_number)
            input_file = BufferedInputFile(qr_image, 'qr.png')

            await call.message.answer_photo(caption=dialogs.RU_ru['user']['card'],
                                            reply_markup=await create_user_menu_card(),
                                            photo=input_file,
                                            protect_content=True)


@user_router.callback_query(F.data.startswith("register_"))
async def register_step(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = call.data.removeprefix('register_')
    if data == 'name':
        await call.message.edit_text(text=dialogs.RU_ru['register']['name'])
        await state.set_state(Register.step)
    if data == 'phone':
        await call.message.delete()
        await bot.send_message(chat_id=call.from_user.id, text=dialogs.RU_ru['register']['phone'],
                               reply_markup=await send_contact())
        await state.set_state(Register.step)
    if data == 'email':
        await call.message.edit_text(text=dialogs.RU_ru['register']['email'])
        await state.set_state(Register.step)
    if data == 'birthday':
        await call.message.edit_text(text=dialogs.RU_ru['register']['birthday'])
        await state.set_state(Register.step)
    if data == 'sex':
        await call.message.edit_text(text=dialogs.RU_ru['register']['sex'], reply_markup=await choose_sex_menu())
    if data == 'male' or data == 'female' or data == 'none':
        sex_list = ['none', 'male', 'female']
        db.query(query='UPDATE customers SET sex=%s WHERE user_id=%s',
                 values=(f'{sex_list.index(data)}', call.from_user.id))
        result = db.query(query="""SELECT name, middlename, surname, birthday, sex, phone, email, referrer_id
                                                       FROM customers WHERE user_id=%s""",
                          values=(call.from_user.id,),
                          fetch='fetchone')
        if result:
            sex_list = [dialogs.RU_ru['navigation']['not_match'], dialogs.RU_ru['navigation']['male'],
                        dialogs.RU_ru['navigation']['female']]
            name, middlename, surname, birthday, sex, phone, email, referrer_id = (
                value if value is not None else dialogs.RU_ru['empty'] for value in result
            )
            promo = db.query("SELECT receive_promo FROM customers WHERE user_id=%s",
                             values=(call.from_user.id,), fetch='fetchone')[0]
            if promo == 'true':
                _promo = '✅'
            else:
                _promo = '❌'

            if referrer_id is not None:
                referrer_name = await find_referrer_name(referrer_id)
            else:
                referrer_name = dialogs.RU_ru['empty']

            if middlename is not None:
                _name = f'{surname} {name} {middlename}'
            else:
                _name = f'{surname} {name}'

            try:
                _sex = sex_list[int(sex)]
            except:
                _sex = sex_list[0]

            await call.message.edit_text(
                text=dialogs.RU_ru['register']['start'].format(us_name=call.from_user.first_name,
                                                               name=_name, birthday=birthday,
                                                               sex=_sex,
                                                               referrer=referrer_name,
                                                               phone=phone, email=email, promo=_promo),
                reply_markup=await create_register_menu())
    if data == 'promo':
        result = db.query(query="""SELECT name, middlename, surname, birthday, sex, phone, email, referrer_id
                                               FROM customers WHERE user_id=%s""", values=(call.from_user.id,),
                          fetch='fetchone')
        promo = \
        db.query("SELECT receive_promo FROM customers WHERE user_id=%s", values=(call.from_user.id,), fetch='fetchone')[
            0]
        if result:
            sex_list = [dialogs.RU_ru['navigation']['not_match'], dialogs.RU_ru['navigation']['male'],
                        dialogs.RU_ru['navigation']['female']]
            name, middlename, surname, birthday, sex, phone, email, referrer_id = (
                value if value is not None else dialogs.RU_ru['empty'] for value in result
            )
            if promo == 'true':
                db.query(query='UPDATE customers SET receive_promo=FALSE WHERE user_id=%s',
                         values=(call.from_user.id,))
                _promo = '❌'
            else:
                db.query(query='UPDATE customers SET receive_promo=TRUE WHERE user_id=%s',
                         values=(call.from_user.id,))
                _promo = '✅'

            if referrer_id is not None:
                referrer_name = await find_referrer_name(referrer_id)
            else:
                referrer_name = dialogs.RU_ru['empty']

            if middlename is not None:
                _name = f'{surname} {name} {middlename}'
            else:
                _name = f'{surname} {name}'

            try:
                _sex = sex_list[int(sex)]
            except:
                _sex = sex_list[0]

            await call.message.edit_text(
                text=dialogs.RU_ru['register']['start'].format(us_name=call.from_user.first_name,
                                                               name=_name, birthday=birthday,
                                                               sex=_sex,
                                                               referrer=referrer_name,
                                                               phone=phone, email=email, promo=_promo),
                reply_markup=await create_register_menu())

    if data == 'save':
        await call.message.edit_text(text=dialogs.RU_ru['register']['consent'], reply_markup=await privacy_keyboard())

    if data == 'privacy_yes' or data == 'privacy_no':
        privacy_list = ['privacy_yes', 'privacy_no']
        db.query(query="UPDATE customers SET consent_status=%s, comment=%s WHERE user_id=%s",
                 values=(f'{privacy_list.index(data) + 1}',
                         'Registered from TelegramBOT', call.from_user.id))

        if await create_update_customer(user_id=call.from_user.id) is True:

            await call.message.edit_text(text=dialogs.RU_ru['register']['save'],
                                         reply_markup=await create_menu_keyboard(call.from_user.id))
        else:
            await call.message.edit_text(text=dialogs.RU_ru['register']['error'])

# @user_router.callback_query(F.data.startswith('settings_'))
# async def settings_menus(call: CallbackQuery):
#     data = call.data.removeprefix('settings_')
#
#     await call.message.edit_text(text=dialogs.RU_ru['settings'].format(items[0], items[1], items[2]),
#                                  reply_markup=await settings_menu())
