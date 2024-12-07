import re

import aiogram.exceptions
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from Bot import dialogs
from Bot.Keyboards.inline_keyboards import admin_menu, create_admin_list_keyboard, \
    create_user_card_menu, create_admin_back_menu, create_user_card_menu_withuot_acc
from Bot.Utils.states import AdminFindUser
from Database.database import db
from Database.database_query import check_stop_list
from Scripts.scripts import normalize_phone_number

admin_router = Router()


# COMMANDS | MESSAGES

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
    name, surname, phone, category = db.query(
        query='SELECT name, surname, phone, category FROM customers WHERE user_id=%s', values=(user_id,),
        fetch='fetchone')
    admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                          fetch='fetchone')
    name = f'{surname} {name}'
    await call.message.edit_text(
        text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
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
        name, surname, phone, category = db.query(
            query='SELECT name, surname, phone, category FROM customers WHERE user_id=%s',
            values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        try:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        except aiogram.exceptions.TelegramBadRequest as _ex:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu_withuot_acc(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['admin_up'], show_alert=True)

    elif data == 'downgrade_to_user':
        db.query(query="UPDATE users SET is_admin=false WHERE user_id=%s",
                 values=(user_id,))
        name, surname, phone, category = db.query(
            query='SELECT name, surname, phone, category FROM customers WHERE user_id=%s',
            values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        try:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        except aiogram.exceptions.TelegramBadRequest as _ex:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu_withuot_acc(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['admin_down'], show_alert=True)

    elif data == 'upgrade_to_smm':
        db.query(query="UPDATE users SET is_smm=TRUE WHERE user_id=%s",
                 values=(user_id,))
        name, surname, phone, category = db.query(
            query='SELECT name, surname, phone, category FROM customers WHERE user_id=%s',
            values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        try:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        except aiogram.exceptions.TelegramBadRequest as _ex:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu_withuot_acc(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['smm_up'], show_alert=True)

    elif data == 'downgrade_from_smm':
        db.query(query="UPDATE users SET is_smm=FALSE WHERE user_id=%s",
                 values=(user_id,))
        name, surname, phone, category = db.query(
            query='SELECT name, surname, phone, category FROM customers WHERE user_id=%s',
            values=(user_id,), fetch='fetchone')
        admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                              fetch='fetchone')
        name = f'{surname} {name}'
        try:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
        except aiogram.exceptions.TelegramBadRequest as _ex:
            await call.message.edit_text(
                text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                    admin=dialogs.RU_ru['marks'][
                                                                        admin],
                                                                    smm=dialogs.RU_ru['marks'][
                                                                        smm],
                                                                    user_id=user_id),
                reply_markup=await create_user_card_menu_withuot_acc(user_id), parse_mode='HTML')
        await call.answer(text=dialogs.RU_ru['notifications']['smm_down'], show_alert=True)


@admin_router.callback_query(F.data == 'find_user_admin')
async def admin_find_user(call: CallbackQuery, state: FSMContext):
    name = db.query(query="SELECT name FROM customers WHERE user_id=%s", values=(call.from_user.id,), fetch='fetchone')[
        0]
    await call.message.edit_text(text=dialogs.RU_ru['admin_find_user'].format(name=name),
                                 reply_markup=await create_admin_back_menu())
    await state.set_state(state=AdminFindUser.user)


# STATES

@admin_router.message(AdminFindUser.user)
async def admin_find_user_state_user(message: Message, state: FSMContext):
    message_text = message.text.strip()
    data = message_text
    phone_pattern = re.compile(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$')
    try:
        if phone_pattern.match(message_text):
            data = await normalize_phone_number(data)
            user_id, name, surname, category = db.query(query=f"""SELECT user_id, name, surname, category FROM customers 
            WHERE phone LIKE %s OR phone LIKE %s""",
                                                        values=(data, f'+{data}'), fetch='fetchone')
            admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                                  fetch='fetchone')
            name = f'{surname} {name}'
            try:
                await message.answer(
                    text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=data, category=category,
                                                                        admin=dialogs.RU_ru['marks'][
                                                                            admin],
                                                                        smm=dialogs.RU_ru['marks'][
                                                                            smm],
                                                                        user_id=user_id),
                    reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
            except aiogram.exceptions.TelegramBadRequest as _ex:
                await message.answer(
                    text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=data, category=category,
                                                                        admin=dialogs.RU_ru['marks'][
                                                                            admin],
                                                                        smm=dialogs.RU_ru['marks'][
                                                                            smm],
                                                                        user_id=user_id),
                    reply_markup=await create_user_card_menu_withuot_acc(user_id), parse_mode='HTML')

        else:
            text = data.split(" ", maxsplit=3)
            if len(text) == 3:
                _surname = text[0]
                _name = text[1]
                _middlename = text[2]
            else:
                _surname = text[0]
                _name = text[1]
                _middlename = None
            user_id, name, surname, category, phone = db.query(
                query="SELECT user_id, name, surname, category, phone FROM customers WHERE (name ILIKE %s AND surname ILIKE %s) OR (name ILIKE %s AND surname ILIKE %s)",
                values=(_name, _surname, _surname, _name), fetch='fetchone')
            admin, smm = db.query(query='SELECT is_admin, is_smm FROM users WHERE user_id=%s', values=(user_id,),
                                  fetch='fetchone')
            name = f'{surname} {name}'
            try:
                await message.answer(
                    text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                        admin=dialogs.RU_ru['marks'][
                                                                            admin],
                                                                        smm=dialogs.RU_ru['marks'][
                                                                            smm],
                                                                        user_id=user_id),
                    reply_markup=await create_user_card_menu(user_id), parse_mode='HTML')
            except aiogram.exceptions.TelegramBadRequest as _ex:
                await message.answer(
                    text=dialogs.RU_ru['user']['user_for_admin'].format(name=name, phone=phone, category=category,
                                                                        admin=dialogs.RU_ru['marks'][
                                                                            admin],
                                                                        smm=dialogs.RU_ru['marks'][
                                                                            smm],
                                                                        user_id=user_id),
                    reply_markup=await create_user_card_menu_withuot_acc(user_id), parse_mode='HTML')
        await state.clear()
    except Exception as _ex:
        print(_ex)
        await message.answer(text=dialogs.RU_ru['not_found_user'].format(data=data), reply_markup=await admin_menu())
        await state.clear()
