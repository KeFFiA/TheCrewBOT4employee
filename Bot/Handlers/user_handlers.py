from asyncio import sleep

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from API_SCRIPTS.iiko_cloudAPI import update_token
from Bot import dialogs
from Bot.Keyboards.inline_keyboards import register_menu, create_menu_keyboard
from Bot.Keyboards.keyboards import send_contact
from Bot.Utils.states import Register
from Bot.dialogs import commands
from Database.database import db

user_router = Router()

# COMMANDS/MESSAGES

@user_router.message(Command("start"))
async def start_cmd(message: Message, bot: Bot, state: FSMContext):
    await bot.set_my_commands(commands=commands)
    await message.answer(dialogs.RU_ru['/start'].format(message.from_user.first_name))
    db.query(
        query="INSERT INTO users (user_id, username, user_name, user_surname) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        values=(
            message.from_user.id, message.from_user.username, message.from_user.first_name,
            message.from_user.last_name),
        log_level=10,
        msg=f'User {message.from_user.id} already exist')

    await state.clear()


@user_router.message(Command("register"))
async def register_cmd(message: Message):
    db.query(query="INSERT INTO employee_list (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
             values=(message.from_user.id,),
             log_level=10,
             msg=f'Employee {message.from_user.id} already exist')

    name, phone = db.query(query="SELECT name, phone FROM employee_list WHERE user_id = %s",
                          values=(message.from_user.id,), fetch='fetchall')[0]

    if name is None:
        name = dialogs.RU_ru['empty']

    if phone is None:
        phone = dialogs.RU_ru['empty']

    sent_message = await message.answer(text=dialogs.RU_ru['register']['start'].format(message.from_user.first_name))
    await sleep(3)
    await sent_message.edit_text(text=dialogs.RU_ru['register']['info'].format(name, phone), reply_markup=await register_menu())


@user_router.message(F.contact)
async def register_contact(message: Message, bot: Bot):
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    except:
        pass
    db.query(query="UPDATE employee_list SET phone=%s WHERE user_id = %s",
             values=(message.contact.phone_number, message.from_user.id))

    name, phone = db.query(query="SELECT name, phone FROM employee_list WHERE user_id = %s",
                           values=(message.from_user.id,), fetch='fetchall')[0]

    if name is None:
        name = dialogs.RU_ru['empty']

    await message.answer(text=dialogs.RU_ru['register']['info'].format(name, phone),
                                 reply_markup=await register_menu())



@user_router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    db.query(query="UPDATE employee_list SET name=%s WHERE user_id = %s",
             values=(message.text, message.from_user.id))

    await update_token()

    name, phone = db.query(query="SELECT name, phone FROM employee_list WHERE user_id = %s",
                           values=(message.from_user.id,), fetch='fetchall')[0]

    if phone is None:
        phone = dialogs.RU_ru['empty']

    await message.answer(text=dialogs.RU_ru['register']['info'].format(name, phone),
                         reply_markup=await register_menu())
    await state.clear()



# CALLBACKS

@user_router.callback_query(F.data.startswith('register_'))
async def register_step(call: CallbackQuery, bot: Bot, state: FSMContext):
    if call.data == 'register_name':
        await call.message.edit_text(text=dialogs.RU_ru['register']['name'])
        await state.set_state(Register.name)
    if call.data == 'register_phone':
        await call.message.delete()
        await bot.send_message(chat_id=call.from_user.id, text=dialogs.RU_ru['register']['phone'], reply_markup=await send_contact())
    if call.data == 'register_save':
        db.query("""UPDATE employee_list
                    SET emp_id = es.employee_id
                    FROM employee_server es
                    WHERE employee_list.name = es.name;""")
        await call.message.edit_text(text=dialogs.RU_ru['register']['save'],
                                     reply_markup=await create_menu_keyboard(call.from_user.id))

