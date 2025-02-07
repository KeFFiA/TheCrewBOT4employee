import re
from token import AWAIT

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from API_SCRIPTS.iiko_cloudAPI import create_update_customer
from Bot import dialogs
from Bot.Keyboards.inline_keyboards import create_menu_keyboard, create_register_menu, choose_sex_menu, \
    privacy_keyboard, create_user_menu_me, create_user_menu_card, settings_menu
from Bot.Keyboards.keyboards import send_contact
from Bot.Utils.states import Register
from Database.database import db
from Scripts.scripts import generate_qr_card, find_referrer_name, normalize_phone_number, find_similar_names

user_router = Router()


# COMMANDS/MESSAGES

@user_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext, command: CommandObject):
    try:
        user_check = db.query(query="SELECT is_registered FROM users WHERE user_id=%s", values=(message.from_user.id,),
                              fetch='fetchone')[0]
    except:
        user_check = False

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


@user_router.message(Command('card'))
async def card_cmd(message: Message, state: FSMContext):
    card_number = db.query(query="""SELECT card_number FROM customers WHERE user_id=%s""", values=(message.from_user.id,),
                           fetch='fetchone')[0]
    qr_image = await generate_qr_card(card_number=card_number)
    input_file = BufferedInputFile(qr_image, 'qr.png')
    await message.answer_photo(caption=dialogs.RU_ru['user']['card'],
                                    reply_markup=await create_user_menu_card(),
                                    photo=input_file,
                                    protect_content=True)
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
            url = f'https://t.me/TheCrewEnergyBot?start={call.from_user.id}'
            try:
                await call.message.edit_text(text=dialogs.RU_ru['user']['info'].format(
                    name=_name, phone=phone, email=email, sex=_sex, referrer=referrer_name,
                    user_id=call.from_user.id, birthday=birthday, category=category, url=url
                ),
                    reply_markup=await create_user_menu_me())
            except:
                await call.message.delete()
                await call.message.answer(text=dialogs.RU_ru['user']['info'].format(
                    name=_name, phone=phone, email=email, sex=_sex, referrer=referrer_name,
                    user_id=call.from_user.id, birthday=birthday, category=category, url=url
                ),
                    reply_markup=await create_user_menu_me())
        if data == 'card':
            try:
                await call.message.delete()
            except:
                pass
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
        name, phone, birthday = db.query("SELECT name, phone, birthday FROM customers WHERE user_id=%s",
                                         values=(call.from_user.id,), fetch='fetchone')
        if name is None or phone is None or birthday is None:
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
                    text=dialogs.RU_ru['register']['fields_error'].format(us_name=call.from_user.first_name,
                                                                   name=_name, birthday=birthday,
                                                                   sex=_sex,
                                                                   referrer=referrer_name,
                                                                   phone=phone, email=email, promo=_promo),
                    reply_markup=await create_register_menu())
        else:
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


@user_router.callback_query(F.data.startswith('settings_'))
async def settings_menus(call: CallbackQuery):
    data = call.data.removeprefix('settings_')
    tg, sms, email = db.query(query="SELECT tg_promo, sms_promo, email_promo FROM users WHERE user_id=%s", values=(call.from_user.id,),
                     fetch='fetchone')

    if data == 'menu':
        await call.message.edit_text(text=dialogs.RU_ru['settings'].format(tg_promo=dialogs.RU_ru['marks'][tg],
                                                                           sms_promo=dialogs.RU_ru['marks'][sms],
                                                                           email_promo=dialogs.RU_ru['marks'][email]),
                                     reply_markup=await settings_menu())
    if data == 'tg_promo':
        if tg:
            db.query(query='UPDATE users SET tg_promo=FALSE WHERE user_id=%s', values=(call.from_user.id,))
            await call.message.edit_text(text=dialogs.RU_ru['settings'].format(tg_promo=dialogs.RU_ru['marks'][False],
                                                                               sms_promo=dialogs.RU_ru['marks'][sms],
                                                                               email_promo=dialogs.RU_ru['marks'][
                                                                                   email]),
                                         reply_markup=await settings_menu())
        else:
            db.query(query='UPDATE users SET tg_promo=TRUE WHERE user_id=%s', values=(call.from_user.id,))
            await call.message.edit_text(text=dialogs.RU_ru['settings'].format(tg_promo=dialogs.RU_ru['marks'][True],
                                                                               sms_promo=dialogs.RU_ru['marks'][sms],
                                                                               email_promo=dialogs.RU_ru['marks'][
                                                                                   email]),
                                         reply_markup=await settings_menu())
    if data == 'sms_promo':
        if sms:
            db.query(query='UPDATE users SET sms_promo=FALSE WHERE user_id=%s', values=(call.from_user.id,))
            await call.message.edit_text(text=dialogs.RU_ru['settings'].format(tg_promo=dialogs.RU_ru['marks'][tg],
                                                                               sms_promo=dialogs.RU_ru['marks'][False],
                                                                               email_promo=dialogs.RU_ru['marks'][
                                                                                   email]),
                                         reply_markup=await settings_menu())
        else:
            db.query(query='UPDATE users SET sms_promo=TRUE WHERE user_id=%s', values=(call.from_user.id,))
            await call.message.edit_text(text=dialogs.RU_ru['settings'].format(tg_promo=dialogs.RU_ru['marks'][tg],
                                                                               sms_promo=dialogs.RU_ru['marks'][True],
                                                                               email_promo=dialogs.RU_ru['marks'][
                                                                                   email]),
                                         reply_markup=await settings_menu())
    if data == 'email_promo':
        if email:
            db.query(query='UPDATE users SET email_promo=FALSE WHERE user_id=%s', values=(call.from_user.id,))
            await call.message.edit_text(text=dialogs.RU_ru['settings'].format(tg_promo=dialogs.RU_ru['marks'][tg],
                                                                               sms_promo=dialogs.RU_ru['marks'][sms],
                                                                               email_promo=dialogs.RU_ru['marks'][
                                                                                   False]),
                                         reply_markup=await settings_menu())
        else:
            db.query(query='UPDATE users SET email_promo=TRUE WHERE user_id=%s', values=(call.from_user.id,))
            await call.message.edit_text(text=dialogs.RU_ru['settings'].format(tg_promo=dialogs.RU_ru['marks'][tg],
                                                                               sms_promo=dialogs.RU_ru['marks'][sms],
                                                                               email_promo=dialogs.RU_ru['marks'][
                                                                                   True]),
                                         reply_markup=await settings_menu())

    tg, sms, email = db.query(query="SELECT tg_promo, sms_promo, email_promo FROM users WHERE user_id=%s",
                              values=(call.from_user.id,),
                              fetch='fetchone')

    if not tg and not sms and not email:
        db.query(query='UPDATE customers SET receive_promo=FALSE WHERE user_id=%s', values=(call.from_user.id,))
        await create_update_customer(call.from_user.id)
    else:
        db.query(query='UPDATE customers SET receive_promo=TRUE WHERE user_id=%s', values=(call.from_user.id,))
        await create_update_customer(call.from_user.id)


# STATES

@user_router.message(Register.step)
async def register_step_1(message: Message, state: FSMContext):
    date_pattern = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
    phone_pattern = re.compile(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$')
    text = message.text.strip()

    if message.entities:
        email = [entity for entity in message.entities if entity.type == 'email']
        phone = [entity for entity in message.entities if entity.type == 'phone_number']
        if email:
            _email = email[0].extract_from(message.text)
            db.query(query="UPDATE customers SET email = %s WHERE user_id=%s", values=(_email, message.from_user.id))
        if phone:
            _phone = await normalize_phone_number(phone[0].extract_from(message.text))
            db.query(query="UPDATE customers SET phone = %s WHERE user_id=%s", values=(f'+{_phone}', message.from_user.id))
    elif date_pattern.match(text):
        birthday = text
        db.query(query="UPDATE customers SET birthday = %s WHERE user_id=%s", values=(birthday, message.from_user.id))
    elif phone_pattern.match(text):
        _phone = await normalize_phone_number(text)
        db.query(query="UPDATE customers SET phone = %s WHERE user_id=%s", values=(f'+{_phone}', message.from_user.id))
    elif not bool(message.entities) and not bool(date_pattern.match(text)) and not bool(phone_pattern.match(text)):
        result = await find_similar_names(text)
        result_test = result[0].split()
        user_id_test = db.query(query='SELECT user_id FROM customers WHERE surname = %s AND name = %s', values=(result_test[0], result_test[1]), fetch='one')[0]
        if not user_id_test:
            if result:
                full_name = result[0].split(" ", maxsplit=3)
                if len(text) == 3:
                    surname = full_name[0]
                    name = full_name[1]
                    middlename = full_name[2] or text[2]
                else:
                    surname = full_name[0]
                    name = full_name[1]
                    middlename = None
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
        elif user_id_test != message.from_user.id:
            text = text.split(" ", maxsplit=3)
            if len(text) == 3:
                surname = text[0]
                name = text[1]
                middlename = text[2]
            else:
                surname = text[0]
                name = text[1]
                middlename = None
        else:
            full_name = result[0].split(" ", maxsplit=3)
            if len(text) == 3:
                surname = full_name[0]
                name = full_name[1]
                middlename = full_name[2] or text[2]
            else:
                surname = full_name[0]
                name = full_name[1]
                middlename = None
        db.query(query="UPDATE customers SET name=%s, surname=%s, middlename=%s WHERE user_id=%s",
                 values=(name, surname, middlename, message.from_user.id))
    else:
        await message.answer(text=dialogs.RU_ru['register']['not_found_match'].format(text=text))
        await state.set_state(Register.step)
        return

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

        if referrer_id is not dialogs.RU_ru['empty']:
            referrer_name = await find_referrer_name(referrer_id)
        else:
            referrer_name = dialogs.RU_ru['empty']

        if middlename is not dialogs.RU_ru['empty']:
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





