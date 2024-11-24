from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from Bot import dialogs
from Bot.Keyboards.inline_keyboards import admin_menu, create_admin_list_keyboard, \
    create_user_card_menu  # , create_white_list_keyboard
from Bot.Utils.states import WhiteList
from Database.database import db
from Database.database_query import check_stop_list

admin_router = Router()

# COMMANDS

@admin_router.message(Command('admin'))
async def admin_cmd(message: Message, state: FSMContext):
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


@admin_router.callback_query(F.data == 'admin_list')
async def white_list(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text=dialogs.RU_ru['admin_list'], reply_markup=await create_admin_list_keyboard())


@admin_router.callback_query(F.data.startswith('admin_'))
async def white_list_press_user(call: CallbackQuery):
    user_id = call.data.removeprefix('admin_')
    name, surname, phone = db.query(query='SELECT name, surname, phone FROM customers WHERE user_id=%s', values=(user_id,), fetch='fetchone')
    admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,), fetch='fetchone')
    name = f'{surname} {name}'
    await call.message.edit_text(text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone,
                                                                           admin=dialogs.RU_ru['marks'][admin],
                                                                           smm=dialogs.RU_ru['marks'][smm],
                                                                           user_id=user_id),
                                 reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')


@admin_router.callback_query(F.data.startswith('white_btn'))
async def white_choose(call: CallbackQuery):
    data = call.data.removeprefix('white_btn_')
    user_id = ''.join([char for char in data if char.isdigit()])
    data = data.removeprefix(f'{user_id}_')

    if data == 'upgrade_to_admin':
        db.query(query="UPDATE users SET is_admin=true WHERE user_id=%s",
                 values=(user_id,))
        name, surname, phone = db.query(query='SELECT name, surname, phone FROM customers WHERE user_id=%s',
                                        values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        await call.message.edit_text(text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone,
                                                                                         admin=dialogs.RU_ru['marks'][
                                                                                             admin],
                                                                                         smm=dialogs.RU_ru['marks'][
                                                                                             smm],
                                                                                         user_id=user_id),
                                     reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['admin_up'], show_alert=True)

    elif data == 'downgrade_to_user':
        db.query(query="UPDATE users SET is_admin=false WHERE user_id=%s",
                 values=(user_id,))
        name, surname, phone = db.query(query='SELECT name, surname, phone FROM customers WHERE user_id=%s',
                                        values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        await call.message.edit_text(text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone,
                                                                                         admin=dialogs.RU_ru['marks'][
                                                                                             admin],
                                                                                         smm=dialogs.RU_ru['marks'][
                                                                                             smm],
                                                                                         user_id=user_id),
                                     reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['admin_down'], show_alert=True)

    elif data == 'upgrade_to_smm':
        db.query(query="UPDATE users SET is_smm=TRUE WHERE user_id=%s",
                 values=(user_id,))
        name, surname, phone = db.query(query='SELECT name, surname, phone FROM customers WHERE user_id=%s',
                                        values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        await call.message.edit_text(text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone,
                                                                                         admin=dialogs.RU_ru['marks'][
                                                                                             admin],
                                                                                         smm=dialogs.RU_ru['marks'][
                                                                                             smm],
                                                                                         user_id=user_id),
                                     reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['smm_up'], show_alert=True)

    elif data == 'downgrade_from_smm':
        db.query(query="UPDATE users SET is_smm=FALSE WHERE user_id=%s",
                 values=(user_id,))
        name, surname, phone = db.query(query='SELECT name, surname, phone FROM customers WHERE user_id=%s',
                                        values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        await call.message.edit_text(text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone,
                                                                                         admin=dialogs.RU_ru['marks'][
                                                                                             admin],
                                                                                         smm=dialogs.RU_ru['marks'][
                                                                                             smm],
                                                                                         user_id=user_id),
                                     reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['smm_down'], show_alert=True)


# MESSAGES
