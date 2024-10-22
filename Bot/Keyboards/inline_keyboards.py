from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from API_SCRIPTS.Iiko_cloudAPI import check_shift, update_token
from Bot import dialogs
from Database.database import db
from Database.database_query import white_list


async def create_menu_keyboard(user_id):
    stats = InlineKeyboardButton(callback_data='stats_stats', text=dialogs.RU_ru['navigation']['stats'])
    settings = InlineKeyboardButton(callback_data='settings_menu', text=dialogs.RU_ru['navigation']['settings'])

    open = InlineKeyboardButton(callback_data='shift_open', text=dialogs.RU_ru['navigation']['open'])
    close = InlineKeyboardButton(callback_data='shift_close', text=dialogs.RU_ru['navigation']['close'])

    keyboard_main = InlineKeyboardMarkup(inline_keyboard=[
        [stats],
        [settings]
    ])

    builder = InlineKeyboardBuilder()

    builder.attach(InlineKeyboardBuilder.from_markup(keyboard_main))

    empl_id = db.query(query="SELECT emp_id FROM employee_list WHERE user_id=%s", values=(user_id,), fetch='fetchone')[0]

    if db.query(query="SELECT employee_id FROM employee_couriers WHERE employee_id=%s", values=(empl_id,)):
        await update_token()

        if await check_shift(empl_id):
            keyboard_attendance = InlineKeyboardMarkup(inline_keyboard=[[close]])
        else:
            keyboard_attendance = InlineKeyboardMarkup(inline_keyboard=[[open]])

        builder.attach(InlineKeyboardBuilder.from_markup(keyboard_attendance))

    admin = db.query(query="SELECT admin FROM white_list WHERE user_id=%s", fetch='fetchone', values=(user_id,))[0]

    if admin:
        admin_but = InlineKeyboardButton(callback_data='admin', text=dialogs.RU_ru['navigation']['admin'])
        admin_kb = InlineKeyboardMarkup(inline_keyboard=[[admin_but]])
        builder.attach(InlineKeyboardBuilder.from_markup(admin_kb))
    return builder.as_markup()


async def register_menu():
    name = InlineKeyboardButton(callback_data='register_name', text=dialogs.RU_ru['navigation']['name'])
    phone = InlineKeyboardButton(callback_data='register_phone', text=dialogs.RU_ru['navigation']['phone'])
    save = InlineKeyboardButton(callback_data='register_save', text=dialogs.RU_ru['navigation']['done'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [name, phone],
        [save]
    ])

    return keyboard


async def choose_menu():
    yes = InlineKeyboardButton(callback_data='yes', text=dialogs.RU_ru['navigation']['yes'])
    no = InlineKeyboardButton(callback_data='no', text=dialogs.RU_ru['navigation']['no'])
    back = InlineKeyboardButton(callback_data='back', text=dialogs.RU_ru['navigation']['back'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [yes, no],
        [back]
    ])

    return keyboard


async def choose_org_menu(user_id):
    builder = InlineKeyboardBuilder()

    emp_id = db.query(query="SELECT emp_id FROM employee_list WHERE user_id=%s", fetch='fetchone', values=(user_id,))[0]
    org_ids = db.query(query="SELECT org_ids FROM employee_couriers WHERE employee_id=%s", values=(emp_id,), fetch='fetchone')[0]
    try:
        org_ids_list = org_ids.replace('{', '').replace('}', '').split(',')
    except:
        org_ids_list = org_ids.replace('{', '').replace('}', '')

    buttons = []
    for org_id in org_ids_list:
        org_name = db.query(query="SELECT name FROM organizations WHERE org_id=%s",
                                     values=(org_id,), fetch='fetchone')[0]

        try:
            buttons.append(InlineKeyboardButton(
                text=org_name,
                callback_data=org_id
            ))
        except Exception as _ex:
            pass

    builder.row(*buttons, width=1)
    back = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['menu'])
    last_btn = InlineKeyboardMarkup(inline_keyboard=[[back]])
    builder.attach(InlineKeyboardBuilder.from_markup(last_btn))

    return builder.as_markup()


async def settings_menu():
    # name = InlineKeyboardButton(callback_data='settings_name', text=dialogs.RU_ru['navigation']['name'])
    # phone = InlineKeyboardButton(callback_data='settings_phone', text=dialogs.RU_ru['navigation']['phone'])
    receive_upd = InlineKeyboardButton(callback_data='settings_receive_upd', text=dialogs.RU_ru['navigation']['receive_upd'])
    receive_time = InlineKeyboardButton(callback_data='settings_receive_time', text=dialogs.RU_ru['navigation']['receive_time'])
    receive_messages = InlineKeyboardButton(callback_data='settings_receive_messages', text=dialogs.RU_ru['navigation']['receive_messages'])

    back = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['back'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # [name, phone],
        [receive_upd, receive_time],
        [receive_messages],
        [back]
    ])

    return keyboard


async def admin_menu():
    white_list_but = InlineKeyboardButton(callback_data='white_list', text=dialogs.RU_ru['navigation']['white_list'])
    stop_list_but = InlineKeyboardButton(callback_data='stop_list', text=dialogs.RU_ru['navigation']['stop_list'])

    back = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['menu'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [white_list_but],
        [stop_list_but],
        [back]
    ])

    return keyboard


async def create_white_list_keyboard():
    builder = InlineKeyboardBuilder()
    button = await white_list()
    buttons = []
    for data, text in button.items():
        try:
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=data
            ))
        except:
            pass

    builder.row(*buttons, width=1)
    last_btn_1 = InlineKeyboardButton(callback_data='next_page', text='-->')
    last_btn_2 = InlineKeyboardButton(callback_data='last_page', text='<--')
    last_btn_3 = InlineKeyboardButton(text=dialogs.RU_ru['navigation']['admin'], callback_data='admin')
    last_btns = InlineKeyboardMarkup(inline_keyboard=[[last_btn_2, last_btn_1], [last_btn_3]])
    builder.attach(InlineKeyboardBuilder.from_markup(last_btns))
    return builder.as_markup()


async def create_choose_time_keyboard():
    now = datetime.now()
    current_day = now.day
    second_half = InlineKeyboardButton(callback_data='stats_second_half', text=dialogs.RU_ru['navigation']['second_half'])
    first_half = InlineKeyboardButton(callback_data='stats_first_half', text=dialogs.RU_ru['navigation']['first_half'])
    this_month = InlineKeyboardButton(callback_data='stats_this_month', text=dialogs.RU_ru['navigation']['this_month'])
    last_month = InlineKeyboardButton(callback_data='stats_last_month', text=dialogs.RU_ru['navigation']['last_month'])
    back = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['menu'])
    if current_day >= 15:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [first_half],
            [this_month],
            [last_month],
            [back]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [second_half],
            [this_month],
            [last_month],
            [back]
        ])
    return keyboard


