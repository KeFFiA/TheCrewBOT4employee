from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from API_SCRIPTS.Iiko_cloudAPI import update_menu, update_stop_list
from Bot import dialogs
from Bot.Keyboards.inline_keyboards import admin_menu, create_white_list_keyboard
from Database.database_query import check_stop_list

admin_router = Router()

# COMMANDS

# @admin_router.message(Command('tokens'), )
# async def tokens(message: Message):


@admin_router.message(Command('admin'))
async def admin(message: Message):
    await message.answer(text=dialogs.RU_ru['admin'], reply_markup=await admin_menu())
    print(await check_stop_list())
    # await update_menu()
    # await update_stop_list()


# CALLBACKS

@admin_router.callback_query(F.data == 'white_list')
async def white_list(call: CallbackQuery):
    await call.message.edit_text(text=dialogs.RU_ru['white_list'], reply_markup=await create_white_list_keyboard())


# MESSAGES
