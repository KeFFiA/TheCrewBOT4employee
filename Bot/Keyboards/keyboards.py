from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from Bot import dialogs


async def send_contact():
    button = KeyboardButton(text=dialogs.RU_ru['navigation']['share'], request_contact=True)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[[button]])

    return keyboard

async def send_location():
    button = KeyboardButton(text=dialogs.RU_ru['navigation']['share'], request_location=True)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[[button]])

    return keyboard