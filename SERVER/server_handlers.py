# -*- coding: utf-8 -*-

import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

import config
from Bot import dialogs
from Bot.Keyboards.inline_keyboards import create_menu_keyboard
from Bot.Utils.logging_settings import server_logger
from Database.database import db

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

async def telegram_webhook(request: web.Request) -> web.Response:
    data = await request.json()

    await dp.feed_raw_update(bot=bot, update=data)

    return web.Response(status=200)


async def iiko_webhook(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        print(data)
        req_token = request.headers.get('Authorization')
        tokens = db.query(query="SELECT token_cloud_endpont FROM tokens", fetch='fetchall')
        for token in tokens:
            if req_token in token:
                req_token = True
        if req_token is True or req_token is None:
            if isinstance(data, list):
                data = data[0]
            event_type = data.get("eventType")
            event_info = data.get("eventInfo")
            if event_type == "PersonalShift":
                if event_info:
                    emp_id = event_info.get("id")
                    if emp_id:
                        user_id = db.query(query="SELECT user_id FROM employee_list WHERE emp_id=%s",
                                           values=(emp_id,),
                                           fetch='fetchone')[0]
                        user_name = db.query(query="SELECT user_name FROM users WHERE user_id=%s", values=(user_id,), fetch='fetchone')[0]
                        try:
                            if event_info.get('opened'):
                                db.query(query="UPDATE employee_list SET time_opened=%s WHERE user_id=%s",
                                         values=(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"), user_id))
                                await bot.send_message(chat_id=user_id,
                                                       text=dialogs.RU_ru['server']['shift_open'].format(user_name,
                                                                                                         datetime.datetime.now().strftime("%H:%M")),
                                                       reply_markup=await create_menu_keyboard(user_id))
                            else:
                                try:
                                    time_opened = db.query(query='SELECT time_opened FROM employee_list WHERE user_id=%s',
                                                           values=(user_id,), fetch='fetchone')[0]
                                    time_now = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                                    time_now = datetime.datetime.strptime(time_now, '%m/%d/%Y %H:%M:%S')
                                    delta = (time_now - datetime.datetime.strptime(time_opened, '%m/%d/%Y %H:%M:%S')).total_seconds()
                                    delta = datetime.timedelta(seconds=delta)
                                    delta = f"{delta.seconds // 3600}:{(delta.seconds // 60) % 60:02}"
                                except:
                                    delta = dialogs.RU_ru['unknown']
                                db.query(query="UPDATE employee_list SET time_opened='' WHERE user_id=%s",
                                         values=(user_id,))
                                await bot.send_message(chat_id=user_id,
                                                       text=dialogs.RU_ru['server']['shift_close'].format(user_name,
                                                                                                          datetime.datetime.now().strftime("%H:%M"),
                                                                                                          delta),
                                                       reply_markup=await create_menu_keyboard(user_id))
                        except Exception as _ex:
                            server_logger.error(f"Failed to send message to {user_id}: {_ex}")
                    else:
                        server_logger.warn('EmployeeID not found from webhook data')
                else:
                    server_logger.error('No data received from iiko_cloud webhook')

            return web.Response(status=200)

        else:
            return web.Response(status=401)
    except Exception as _ex:
        server_logger.exception(f'Webhook handler error: {_ex}')
        return web.Response(status=500)
