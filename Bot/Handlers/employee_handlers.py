from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from API_SCRIPTS.GeoAPI import check_geo
from API_SCRIPTS.Iiko_cloudAPI import shift_close, shift_open
from API_SCRIPTS.iikoAPI import employees_attendance
from Bot import dialogs
from Bot.Keyboards.inline_keyboards import create_menu_keyboard, choose_menu, choose_org_menu, settings_menu, \
    create_choose_time_keyboard
from Bot.Keyboards.keyboards import send_location
from Bot.Utils.states import Choose
from Database.database import db

employee_router = Router()

# COMMANDS/MESSAGES

@employee_router.message(Command('menu'))
async def menu_cmd(message: Message, state: FSMContext):
    await message.answer(text=dialogs.RU_ru['navigation']['menu'],
                         reply_markup=await create_menu_keyboard(message.from_user.id)
                         )
    await state.clear()


@employee_router.message(F.location)
async def location(message: Message, bot: Bot, state: FSMContext):
    if await check_geo(message.location.longitude, message.location.latitude):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        except:
            pass

        await message.answer(text=dialogs.RU_ru['shift']['open']['location_success'],
                             reply_markup=await choose_org_menu(message.from_user.id))
        await state.set_state(Choose.choose_org)

    else:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        except:
            pass

        await message.answer(text=dialogs.RU_ru['shift']['open']['location_fail'],
                                reply_markup=await create_menu_keyboard(message.from_user.id))
        await state.clear()


# CALLBACKS

@employee_router.callback_query(F.data == 'main_menu')
async def white_list_call(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text=dialogs.RU_ru['navigation']['menu'],
                                 reply_markup=await create_menu_keyboard(call.from_user.id)
                                 )

@employee_router.callback_query(F.data.startswith('shift_'))
async def shift(call: CallbackQuery, state: FSMContext):
    if call.data == 'shift_open':
        await call.message.edit_text(text=dialogs.RU_ru['shift']['sure_open'].format(call.from_user.first_name),
                                     reply_markup=await choose_menu())
    if call.data == 'shift_close':
        await call.message.edit_text(text=dialogs.RU_ru['shift']['sure_close'].format(call.from_user.first_name),
                                     reply_markup=await choose_menu())
    await state.update_data(choose=call.data)
    await state.set_state(Choose.choose)


@employee_router.callback_query(Choose.choose)
async def choose(call: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    if data['choose'] == 'shift_close':
        if call.data == 'yes':
            if await shift_close(call.from_user.id):
                await call.message.delete()
            else:
                await call.message.edit_text(text=dialogs.RU_ru['error'].format(call.from_user.first_name),
                                             reply_markup=await create_menu_keyboard(call.from_user.id))
        else:
            await call.message.edit_text(text=dialogs.RU_ru['navigation']['menu'],
                                         reply_markup=await create_menu_keyboard(call.from_user.id))

    elif data['choose'] == 'shift_open':
        if call.data == 'yes':
            await call.message.delete()
            await bot.send_message(chat_id=call.from_user.id,
                                   text=dialogs.RU_ru['shift']['open']['location'].format(call.from_user.first_name),
                                   reply_markup=await send_location())
        else:
            await call.message.edit_text(text=dialogs.RU_ru['navigation']['menu'],
                                         reply_markup=await create_menu_keyboard(call.from_user.id))

    await state.clear()


@employee_router.callback_query(Choose.choose_org)
async def choose_org(call: CallbackQuery, state: FSMContext):
    if await shift_open(call.from_user.id, call.data):
        # await call.message.edit_text(text=dialogs.RU_ru['shift']['open_success'].format(datetime.now().strftime("%m/%d/%Y - %H:%M:%S")),
        #                              reply_markup=await create_menu_keyboard(call.from_user.id))
        await call.message.delete()
    else:
        await call.message.edit_text(text=dialogs.RU_ru['error'].format(call.from_user.first_name),
                                     reply_markup=await create_menu_keyboard(call.from_user.id))
    await state.clear()


@employee_router.callback_query(F.data.startswith('settings_'))
async def settings_menus(call: CallbackQuery):
    data = call.data.removeprefix('settings_')
    name, phone, receive = db.query(
        query="SELECT name, phone, (receive_upd_shift, receive_shift_time, receive_messages) FROM employee_list WHERE user_id=%s",
        values=(call.from_user.id,), fetch='fetchone')

    items = []
    for item in receive.replace('(', '').replace(')', '').split(','):
        if item == 't':
            item = '✅'
        else:
            item = '❌'
        items.append(item)

    if data == 'receive_upd':
        if items[0] == '✅':
            db.query(query="UPDATE employee_list SET receive_upd_shift=FALSE WHERE user_id=%s",
                     values=(call.from_user.id,))
        else:
            db.query(query="UPDATE employee_list SET receive_upd_shift=TRUE WHERE user_id=%s",
                     values=(call.from_user.id,))
    if data == 'receive_time':
        if items[1] == '✅':
            db.query(query="UPDATE employee_list SET receive_shift_time=FALSE WHERE user_id=%s",
                     values=(call.from_user.id,))
        else:
            db.query(query="UPDATE employee_list SET receive_shift_time=TRUE WHERE user_id=%s",
                     values=(call.from_user.id,))
    if data == 'receive_messages':
        if items[2] == '✅':
            db.query(query="UPDATE employee_list SET receive_messages=FALSE WHERE user_id=%s",
                     values=(call.from_user.id,))
        else:
            db.query(query="UPDATE employee_list SET receive_messages=TRUE WHERE user_id=%s",
                     values=(call.from_user.id,))

    name, phone, receive = db.query(
        query="SELECT name, phone, (receive_upd_shift, receive_shift_time, receive_messages) FROM employee_list WHERE user_id=%s",
        values=(call.from_user.id,), fetch='fetchone')

    items = []
    for item in receive.replace('(', '').replace(')', '').split(','):
        if item == 't':
            item = '✅'
        else:
            item = '❌'
        items.append(item)
    await call.message.edit_text(text=dialogs.RU_ru['settings'].format(name, phone, items[0], items[1], items[2]),
                                 reply_markup=await settings_menu())


@employee_router.callback_query(F.data.startswith('stats'))
async def stats_menus(call: CallbackQuery):
    data = call.data.removeprefix('stats_')
    name = db.query(query="SELECT name FROM employee_list WHERE user_id=%s", values=(call.from_user.id,), fetch='fetchone')[0]
    if data == 'stats':
        await call.message.edit_text(text=dialogs.RU_ru['stats'].format(name=name, hours=dialogs.RU_ru['choose_time']['text'],
                                                                        table=dialogs.RU_ru['choose_time']['table']),
                                     reply_markup=await create_choose_time_keyboard(), parse_mode='MARKDOWN')
    else:
        table, result = await employees_attendance(user_id=call.from_user.id, data=data)
        try:
            await call.message.edit_text(
                text=dialogs.RU_ru['stats'].format(name=name, hours=result, table=table),
                reply_markup=await create_choose_time_keyboard(), parse_mode='MARKDOWN')
        except:
            await call.answer()


