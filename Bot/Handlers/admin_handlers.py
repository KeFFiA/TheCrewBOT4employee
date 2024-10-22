from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from Bot import dialogs
from Bot.Keyboards.inline_keyboards import admin_menu, create_white_list_keyboard
from Bot.Utils.states import WhiteList
from Database.database import db
from Database.database_query import check_stop_list

admin_router = Router()

# COMMANDS

@admin_router.message(Command('admin'))
async def admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=dialogs.RU_ru['admin'], reply_markup=await admin_menu())


# CALLBACKS

@admin_router.callback_query(F.data == 'admin')
async def admin_call(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text=dialogs.RU_ru['admin'], reply_markup=await admin_menu())


@admin_router.callback_query(F.data == 'stop_list')
async def stop_list_query(call: CallbackQuery):
    result = await check_stop_list()
    stop_text = ''
    for k, items in result.items():
        stop_text += f'<b>{k}</b>\n\n'
        for item in items.get('items'):
            name = item.get('name')
            stop_text += f'<b>{name}</b>\n'
        stop_text += '\n'

    await call.message.edit_text(text=dialogs.RU_ru['stop_list'].format(stop_text),
                                 reply_markup=await admin_menu())


@admin_router.callback_query(F.data == 'white_list')
async def white_list(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text=dialogs.RU_ru['white_list'], reply_markup=await create_white_list_keyboard())
    await state.set_state(WhiteList.user)


@admin_router.callback_query(F.data.startswith('white_'), WhiteList.user)
async def white_list_press_user(call: CallbackQuery, state: FSMContext):
    user_id = call.data.removeprefix('white_')
    await state.update_data(user_id=user_id)

    username = db.query(query="SELECT username FROM users WHERE user_id=%s", values=(user_id,), fetch='fetchone')[0]

    try:
        name, phone = db.query(query="SELECT name, phone FROM employee_list where user_id=%s", values=(user_id,),
                         fetch='fetchall')[0]
    except:
        name, phone = dialogs.RU_ru['user']['not_registered'], dialogs.RU_ru['user']['not_registered']

    is_admin = db.query(query="SELECT admin FROM white_list WHERE user_id=%s",
                        values=(user_id,), fetch='fetchone')[0]

    inline_btn_delete_user = InlineKeyboardButton(callback_data='white_btn_delete_from_white_list',
                                                  text=dialogs.RU_ru['navigation']['delete'])
    inline_btn_upgrade_user = InlineKeyboardButton(callback_data='white_btn_upgrade_to_admin',
                                                   text=dialogs.RU_ru['navigation']['upgrade'])
    inline_btn_downgrade_user = InlineKeyboardButton(callback_data='white_btn_downgrade_to_user',
                                                     text=dialogs.RU_ru['navigation']['downgrade'])
    inline_btn_back_user = InlineKeyboardButton(callback_data='white_list',
                                                text=dialogs.RU_ru['navigation']['back'])
    inline_btn_acc_user = InlineKeyboardButton(url=f'tg://user?id={user_id}',
                                               text=dialogs.RU_ru['navigation']['message'])
    inline_btn_back_menu = InlineKeyboardButton(text=dialogs.RU_ru['navigation']['admin'], callback_data='admin')

    if is_admin:
        admin = 'true'
        inline_kb_user = InlineKeyboardMarkup(inline_keyboard=[
            [inline_btn_acc_user],
            [inline_btn_downgrade_user, inline_btn_delete_user],
            [inline_btn_back_user],
            [inline_btn_back_menu]
        ])
    else:
        admin = 'false'
        inline_kb_user = InlineKeyboardMarkup(inline_keyboard=[
            [inline_btn_acc_user],
            [inline_btn_upgrade_user, inline_btn_delete_user],
            [inline_btn_back_user],
            [inline_btn_back_menu]
        ])
    await call.message.edit_text(text=dialogs.RU_ru['user']['text'].format(name, phone, username,
                                                                           dialogs.RU_ru['user']['is_admin'][admin],
                                                                           user_id),
                                 reply_markup=inline_kb_user, parse_mode='HTML')
    await state.set_state(WhiteList.choose)


@admin_router.callback_query(F.data.startswith('white_btn'), WhiteList.choose)
async def white_choose(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    choose = call.data
    username = db.query(query="SELECT username FROM users WHERE user_id=%s", values=(data['user_id'],), fetch='fetchone')[0]
    try:
        name, phone = db.query(query="SELECT name, phone FROM employee_list where user_id=%s", values=(data['user_id'],),
                         fetch='fetchall')[0]
    except IndexError:
        name, phone = dialogs.RU_ru['user']['not_registered'], dialogs.RU_ru['user']['not_registered']

    inline_btn_delete_user = InlineKeyboardButton(callback_data='white_btn_delete_from_white_list',
                                                  text=dialogs.RU_ru['navigation']['delete'])
    inline_btn_upgrade_user = InlineKeyboardButton(callback_data='white_btn_upgrade_to_admin',
                                                   text=dialogs.RU_ru['navigation']['upgrade'])
    inline_btn_downgrade_user = InlineKeyboardButton(callback_data='white_btn_downgrade_to_user',
                                                     text=dialogs.RU_ru['navigation']['downgrade'])
    inline_btn_back_user = InlineKeyboardButton(callback_data='white_list',
                                                text=dialogs.RU_ru['navigation']['back'])
    inline_btn_acc_user = InlineKeyboardButton(url=f'tg://user?id={data['user_id']}',
                                               text=dialogs.RU_ru['navigation']['message'])
    inline_btn_back_menu = InlineKeyboardButton(text=dialogs.RU_ru['navigation']['admin'], callback_data='admin')

    if choose == 'white_btn_delete_from_white_list':
        db.query(query="DELETE FROM white_list WHERE user_id=%s",
                 values=(data['user_id'],))

        await call.message.answer(text=dialogs.RU_ru['user']['actions']['deleted'], show_alert=True)
        await state.update_data(user_id='', user_data='')
        await call.message.edit_text(dialogs.RU_ru['white_list'], reply_markup=await create_white_list_keyboard())
        await state.set_state(WhiteList.user)

    elif choose == 'white_btn_upgrade_to_admin':
        db.query(query="UPDATE white_list SET admin=true WHERE user_id=%s",
                 values=(data['user_id'],))
        await call.answer(text='Сотрудник повышен до администратора', show_alert=True)

        inline_kb_user = InlineKeyboardMarkup(inline_keyboard=[
            [inline_btn_acc_user],
            [inline_btn_downgrade_user, inline_btn_delete_user],
            [inline_btn_back_user],
            [inline_btn_back_menu]
        ])

        await call.message.edit_text(text=dialogs.RU_ru['user']['text'].format(name, phone, username,
                                                                               dialogs.RU_ru['user']['is_admin']['true'],
                                                                               data['user_id']),
                                     reply_markup=inline_kb_user, parse_mode='HTML')

    elif choose == 'white_btn_downgrade_to_user':
        db.query(query="UPDATE white_list SET admin=false WHERE user_id=%s",
                 values=(data['user_id'],))

        await call.answer(text='Сотрудник понижен до пользователя', show_alert=True)
        inline_kb_user = InlineKeyboardMarkup(inline_keyboard=[
            [inline_btn_acc_user],
            [inline_btn_upgrade_user, inline_btn_delete_user],
            [inline_btn_back_user],
            [inline_btn_back_menu]
        ])

        await call.message.edit_text(text=dialogs.RU_ru['user']['text'].format(name, phone, username,
                                                                               dialogs.RU_ru['user']['is_admin']['false'],
                                                                               data['user_id']),
                                     reply_markup=inline_kb_user, parse_mode='HTML')


# MESSAGES
