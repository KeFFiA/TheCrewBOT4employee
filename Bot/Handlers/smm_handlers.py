from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from Bot import dialogs
from Bot.Keyboards.inline_keyboards import create_smm_keyboard, create_mailing_keyboard, create_check_mailing_keyboard, \
    create_edit_message_keyboard, create_back_apply_keyboard, create_footer_keyboard
from Bot.Utils.MessageBuilder import msg_builder
from Bot.Utils.states import MsgBuilder
from Database.database import db
from Scripts.scripts import formatting_text

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
    data = call.data.removeprefix('mark_')
    if data == 'create_mailing':
        await call.message.edit_text(text=dialogs.RU_ru['marketing']['create_mailing'], reply_markup=await create_mailing_keyboard())
    if data == 'check_mailings':
        await call.message.edit_text(text=dialogs.RU_ru['marketing']['check_mailings'], reply_markup=await create_check_mailing_keyboard())


@marketing_router.callback_query(F.data.startswith('mailing_'))
async def mailing_menu(call: CallbackQuery, state: FSMContext):
    data = call.data.removeprefix('mailing_')
    if data.startswith('create_'):
        data = data.removeprefix('create_')
        if data == 'momental':
            await call.message.edit_text(text=dialogs.RU_ru['marketing']['mailing']['momental'].format(
                name='',
                time='',
                text='',
                footer='',
                buttons=0,
                media=0
            ), reply_markup=await create_edit_message_keyboard())
        if data == 'scheduler':
            await call.message.edit_text(text=dialogs.RU_ru['marketing']['mailing']['schedule'].format(
                name='',
                time='',
                text='',
                footer='',
                buttons=0,
                media=0
            ), reply_markup=await create_edit_message_keyboard(scheduler=True))
    elif data.startswith('edit_'):
        data = data.removeprefix('edit_')
        print(data)
        if data.startswith('footer'):
            data = data.removeprefix('footer')
            if data == '_farina' or data == '_mad' or data == '_cheb' or data == '_thecrew':
                data = 'footer'.join(data)
                await state.set_data(data={'edit': data})
                await state.set_state(MsgBuilder.edit)
            else:
                await call.message.edit_text(text='Выберите готовый или введите свой', reply_markup=await create_footer_keyboard())  # TODO: Исправить на диалоги
                await state.set_data(data={'edit': 'footer'})
                await state.set_state(MsgBuilder.edit)
        else:
            await call.message.edit_text(text='Ввод:') # TODO: Исправить на диалоги
            await state.set_data(data={'edit': data})
            await state.set_state(MsgBuilder.edit)
    else:
        data = data.removeprefix('check_')
        if data == 'momental':
            result = await msg_builder.build_message()
            try:
                _buttons = result.get('reply_markup', [])
                buttons = _buttons.copy()
            except:
                buttons = InlineKeyboardBuilder()
            buttons.attach(InlineKeyboardBuilder.from_markup(await create_back_apply_keyboard()))
            keyboard = buttons.as_markup()
            name = ''
            time = ''
            footer = ''
            but_len = await msg_builder.get_buttons_len()
            if result.get('media'):
                await call.message.answer_media_group(media=result.get('media'))
                await call.message.answer(text=result.get('text'), reply_markup=keyboard)
            else:
                await call.message.edit_text(text=dialogs.RU_ru['marketing']['mailing']['momental'].format(
                    name=name if name else '',
                    time=time if time else '',
                    text=result['text'],
                    footer=footer if footer else '',
                    buttons=but_len,
                    media=0
                ), reply_markup=keyboard, parse_mode='HTML')
        if data == 'schedule':
            ...


# STATES

@marketing_router.message(MsgBuilder.edit)
async def mailing_edit_step(message: Message, state: FSMContext):
    _data = await state.get_data()
    data = _data['edit']
    if data == 'name':
        await msg_builder.set_name(text=message.text)
    if data == 'text':
        if message.entities:
            text = await formatting_text(message=message.text, entities=message.entities)
            await msg_builder.set_text(text=text)
        else:
            await msg_builder.set_text(text=message.text)
    if data.startswith('footer'):
        print(data)
        data = data.removeprefix('footer')
        if data == 'footer':
            text = message.text
        else:
            text = db.query(query='SELECT text FROM ')
        # elif data == 'mad':
        #     ...
        # elif data == 'cheb':
        #     ...
        # elif data == 'thecrew':
        #     ...
        # else:
        #     await msg_builder.set_footer(text=message.text)
    if data == 'schedule':
        await msg_builder.set_schedule(schedule=message.text)
    if data == 'button':
        text, url = message.text.split()
        await msg_builder.add_button(text=text, url=url)
    if data == 'del_button':
        ...
    if data == 'media':
        if message.entities:
            url_list = [entity for entity in message.entities if entity.type == 'url']
            for url in url_list:
                await msg_builder.add_media(media_type='video', media=url)
        else:
            for i, _ in message:
                if i == 'photo' and _ is not None:
                    await msg_builder.add_media(media_type='photo', media=message.photo[-1].file_id)
                if i == 'video' and _ is not None:
                    await msg_builder.add_media(media_type='video', media=message.video[-1].file_id)

    if data == 'del_media':
        ...
    if data == 'clear':
        await msg_builder.clear()
    name = await msg_builder.get_name()
    time = await msg_builder.get_scheduler()
    text = await msg_builder.get_text()
    footer = await msg_builder.get_footer()
    buttons = await msg_builder.get_buttons_len()
    media = await msg_builder.get_media()
    schedule = ''
    for i in time:
        if i is None:
            schedule += ''
        else:
            schedule += '{i} '
    if name:
        print(True)
        _ = 'schedule'
    else:
        print(False)
        _ = 'momental'

    await message.answer(text=dialogs.RU_ru['marketing']['mailing'][_].format(
        name=name if name else '',
        time=schedule if schedule else '',
        text=text if text else '',
        footer=footer if footer else '',
        buttons=buttons,
        media=len(media)
    ), reply_markup=await create_edit_message_keyboard(), parse_mode='HTML')
    await state.clear()
