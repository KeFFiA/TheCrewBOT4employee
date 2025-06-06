from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import config
from API_SCRIPTS.iikoAPI import bot, dp
from API_SCRIPTS.iiko_cloudAPI import update_token
from Bot.Handlers.admin_handlers import admin_router
from Bot.Handlers.employee_handlers import employee_router
from Bot.Handlers.smm_handlers import marketing_router
from Bot.Handlers.user_handlers import user_router
from Bot.Utils.logging_settings import bot_logger
from Bot.Utils.middlewares import CheckInAdminListMiddleware, CheckInEmployeeListMiddleware
from Bot.Utils.scheduler import load_jobs, scheduler
from Bot.dialogs import commands
from SERVER.SERVER import app, start_server

async def on_startup():
    load_jobs()
    scheduler.start()
    await bot.set_webhook(f'{config.base_url}{config.path_webhook}')
    await bot.set_my_commands(commands=commands)
    await update_token()
    bot_logger.info("Webhook for Telegram set up complete")
    bot_logger.info("Bot started")


async def on_shutdown():
    bot_logger.info("Webhook shutdown complete")
    bot_logger.info("Bot shutdown")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    scheduler.shutdown()


def main():
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(employee_router)
    dp.include_router(marketing_router)

    dp.message.middleware(ChatActionMiddleware())

    admin_router.message.middleware(CheckInAdminListMiddleware())
    admin_router.callback_query.middleware(CheckInAdminListMiddleware())

    employee_router.message.middleware(CheckInEmployeeListMiddleware())
    employee_router.callback_query.middleware(CheckInEmployeeListMiddleware())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    webhook_request_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_request_handler.register(app, path=f'{config.path_webhook}')

    setup_application(app, dp, bot=bot)

    start_server()


if __name__ == "__main__":
    try:
        bot_logger.info("Starting BOT...")
        main()
    except Exception as _ex:
        bot_logger.critical(f'Starting BOT failed with error: {_ex}')
