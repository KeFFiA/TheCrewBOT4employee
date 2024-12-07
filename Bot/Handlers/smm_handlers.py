from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from Bot import dialogs
from Bot.Keyboards.inline_keyboards import create_smm_keyboard, create_mailing_keyboard, create_check_mailing_keyboard, \
    create_edit_message_keyboard

marketing_router = Router()

# MESSAGES | COMMANDS

@marketing_router.message(Command('marketing'))
async def marketing_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=dialogs.RU_ru['marketing']['marketing_menu'], reply_markup=await create_smm_keyboard())

# CALLBACKS

@marketing_router.callback_query(F.data == 'marketing')
async def marketing_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text=dialogs.RU_ru['marketing']['marketing_menu'], reply_markup=await create_smm_keyboard())


@marketing_router.callback_query(F.data.startswith('mark_'))
async def marketing_menu_2(call: CallbackQuery):
    data = call.data.removesuffix('mark_')
    if data == 'create_mailing':
        await call.message.edit_text(text=dialogs.RU_ru['marketing']['create_mailing'], reply_markup=await create_mailing_keyboard())
    if data == 'check_mailings':
        await call.message.edit_text(text=dialogs.RU_ru['marketing']['check_mailings'], reply_markup=await create_check_mailing_keyboard())


@marketing_router.callback_query(F.data.startswith('mailing_'))
async def mailing_menu(call: CallbackQuery):
    data = call.data.removesuffix('mailing_')
    if data.startswith('create_'):
        data = data.removesuffix('create_')
        if data == 'momental':
            await call.message.edit_text(text=dialogs.RU_ru['marketing']['mailing']['momental'].format(
                header=' ',
                body=' ',
                footer=' '
            ), reply_markup=await create_edit_message_keyboard())
        if data == 'scheduler':
            await call.message.edit_text(text=dialogs.RU_ru['marketing']['mailing']['schedule'].format(
                name=dialogs.RU_ru['empty'],
                header=' ',
                body=' ',
                footer=' '
            ), reply_markup=await create_edit_message_keyboard(scheduler=True))
    else:
        data = data.removesuffix('check_')
        if data == 'momental':
            ...
        if data == 'schedule':
            ...


# STATES


