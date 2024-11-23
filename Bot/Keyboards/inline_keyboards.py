from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from API_SCRIPTS.iiko_cloudAPI import check_shift
from Bot import dialogs
from Database.database import db


# from Database.database_query import white_list


async def create_menu_keyboard(user_id):
    settings = InlineKeyboardButton(callback_data='settings_menu', text=dialogs.RU_ru['navigation']['settings'])
    me = InlineKeyboardButton(callback_data='iiko_me', text=dialogs.RU_ru['navigation']['me'])
    card = InlineKeyboardButton(callback_data='iiko_card', text=dialogs.RU_ru['navigation']['card'])

    keyboard_main = InlineKeyboardMarkup(inline_keyboard=[
        [card],
        [me],
        [settings]
    ])

    builder = InlineKeyboardBuilder()
    builder.attach(InlineKeyboardBuilder.from_markup(keyboard_main))
    is_employee = db.query(query='SELECT is_employee FROM users WHERE user_id=%s', values=(user_id,), fetch='fetchone')[0]
    if is_employee is True:
        empl_butn = InlineKeyboardButton(callback_data='employee', text=dialogs.RU_ru['navigation']['employee_menu'])
        empl_kb = InlineKeyboardMarkup(inline_keyboard=[[empl_butn]])
        builder.attach(InlineKeyboardBuilder.from_markup(empl_kb))

    is_admin = db.query(query="SELECT is_admin FROM users WHERE user_id=%s", fetch='fetchone', values=(user_id,))[0]
    if is_admin is True:
        admin_but = InlineKeyboardButton(callback_data='admin', text=dialogs.RU_ru['navigation']['admin_menu'])
        admin_kb = InlineKeyboardMarkup(inline_keyboard=[[admin_but]])
        builder.attach(InlineKeyboardBuilder.from_markup(admin_kb))
    return builder.as_markup()


async def create_employee_menu(user_id):
    stats = InlineKeyboardButton(callback_data='stats_stats', text=dialogs.RU_ru['navigation']['stats'])
    open = InlineKeyboardButton(callback_data='shift_open', text=dialogs.RU_ru['navigation']['open'])
    close = InlineKeyboardButton(callback_data='shift_close', text=dialogs.RU_ru['navigation']['close'])
    menu = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['menu'])
    settings = InlineKeyboardButton(callback_data='employee_settings_menu', text=dialogs.RU_ru['navigation']['settings'])

    builder = InlineKeyboardBuilder()
    keyboard_main = InlineKeyboardMarkup(inline_keyboard=[[stats], [settings]])
    builder.attach(InlineKeyboardBuilder.from_markup(keyboard_main))

    empl_id = db.query(query="SELECT emp_id FROM employee_list WHERE user_id=%s", values=(user_id,), fetch='fetchone')[0]
    if db.query(query="SELECT employee_id FROM employee_couriers WHERE employee_id=%s", values=(empl_id,),
                fetch='fetchone')[0] == empl_id:

        if await check_shift(empl_id):
            keyboard_attendance = InlineKeyboardMarkup(inline_keyboard=[[close], [menu]])
        else:
            keyboard_attendance = InlineKeyboardMarkup(inline_keyboard=[[open], [menu]])

        builder.attach(InlineKeyboardBuilder.from_markup(keyboard_attendance))

    return builder.as_markup()




async def create_user_menu_me():
    card = InlineKeyboardButton(callback_data='iiko_card', text=dialogs.RU_ru['navigation']['card'])
    menu = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['menu'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[card], [menu]])

    return keyboard


async def create_user_menu_card():
    me = InlineKeyboardButton(callback_data='iiko_me', text=dialogs.RU_ru['navigation']['me'])
    menu = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['menu'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[me], [menu]])

    return keyboard


async def create_register_menu():
    name = InlineKeyboardButton(callback_data='register_name', text=dialogs.RU_ru['navigation']['name'])
    phone = InlineKeyboardButton(callback_data='register_phone', text=dialogs.RU_ru['navigation']['phone'])
    email = InlineKeyboardButton(callback_data='register_email', text=dialogs.RU_ru['navigation']['email'])
    birthday = InlineKeyboardButton(callback_data='register_birthday', text=dialogs.RU_ru['navigation']['birthday'])
    sex = InlineKeyboardButton(callback_data='register_sex', text=dialogs.RU_ru['navigation']['sex'])
    receive_promo = InlineKeyboardButton(callback_data='register_promo', text=dialogs.RU_ru['navigation']['promo'])
    save = InlineKeyboardButton(callback_data='register_save', text=dialogs.RU_ru['navigation']['save'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [name, birthday],
        [phone, email],
        [sex],
        [receive_promo],
        [save]
    ])

    return keyboard


async def choose_sex_menu():
    male = InlineKeyboardButton(callback_data='register_male', text=dialogs.RU_ru['navigation']['male'])
    female = InlineKeyboardButton(callback_data='register_female', text=dialogs.RU_ru['navigation']['female'])
    none = InlineKeyboardButton(callback_data='register_none', text=dialogs.RU_ru['navigation']['not_match'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [male, female],
        [none]
    ])

    return keyboard


async def privacy_keyboard():
    yes = InlineKeyboardButton(callback_data='register_privacy_yes', text=dialogs.RU_ru['navigation']['yes'])
    no = InlineKeyboardButton(callback_data='register_privacy_no', text=dialogs.RU_ru['navigation']['no'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[yes, no]])

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

    emp_id = db.query(query="SELECT emp_id FROM employee_list WHERE user_id=%s", fetch='fetchone', values=(user_id,),
                      log_level=30, debug=True)[0]
    org_ids = \
    db.query(query="SELECT org_ids FROM employee_couriers WHERE employee_id=%s", values=(emp_id,), fetch='fetchone',
             log_level=30, debug=True)[0]
    try:
        org_ids_list = org_ids.replace('{', '').replace('}', '').split(',')
    except:
        org_ids_list = org_ids.replace('{', '').replace('}', '')

    buttons = []
    for org_id in org_ids_list:
        org_name = db.query(query="SELECT name FROM organizations WHERE org_id=%s",
                            values=(org_id,), fetch='fetchone', log_level=30, debug=True)[0]

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


async def employee_settings_menu():
    receive_upd = InlineKeyboardButton(callback_data='settings_receive_upd',
                                       text=dialogs.RU_ru['navigation']['receive_upd'])
    receive_time = InlineKeyboardButton(callback_data='settings_receive_time',
                                        text=dialogs.RU_ru['navigation']['receive_time'])
    receive_messages = InlineKeyboardButton(callback_data='settings_receive_messages',
                                            text=dialogs.RU_ru['navigation']['receive_messages'])

    back = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['back'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [receive_upd, receive_time],
        [receive_messages],
        [back]
    ])

    return keyboard


async def settings_menu():
    tg_promo = InlineKeyboardButton(callback_data='settings_tg_promo', text=dialogs.RU_ru['navigation']['tg_promo'])
    sms_promo = InlineKeyboardButton(callback_data='settings_sms_promo', text=dialogs.RU_ru['navigation']['sms_promo'])
    email_promo = InlineKeyboardButton(callback_data='settings_email_promo', text=dialogs.RU_ru['navigation']['email_promo'])
    back = InlineKeyboardButton(callback_data='main_menu', text=dialogs.RU_ru['navigation']['back'])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[tg_promo, sms_promo],
                                                     [email_promo],
                                                     [back]])

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


# async def create_white_list_keyboard():
#     builder = InlineKeyboardBuilder()
#     button = await white_list()
#     buttons = []
#     for data, text in button.items():
#         try:
#             buttons.append(InlineKeyboardButton(
#                 text=text,
#                 callback_data=data
#             ))
#         except:
#             pass
#
#     builder.row(*buttons, width=1)
#     last_btn_1 = InlineKeyboardButton(callback_data='next_page', text='-->')
#     last_btn_2 = InlineKeyboardButton(callback_data='last_page', text='<--')
#     last_btn_3 = InlineKeyboardButton(text=dialogs.RU_ru['navigation']['admin'], callback_data='admin')
#     last_btns = InlineKeyboardMarkup(inline_keyboard=[[last_btn_2, last_btn_1], [last_btn_3]])
#     builder.attach(InlineKeyboardBuilder.from_markup(last_btns))
#     return builder.as_markup()


async def create_choose_time_keyboard():
    now = datetime.now()
    current_day = now.day
    second_half = InlineKeyboardButton(callback_data='stats_second_half',
                                       text=dialogs.RU_ru['navigation']['second_half'])
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
