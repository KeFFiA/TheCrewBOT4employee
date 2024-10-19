from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import config
from Bot.Handlers.admin_handlers import admin_router
from Bot.Handlers.user_handlers import user_router
from Bot.Handlers.employee_handlers import employee_router
from Bot.Utils.logging_settings import bot_logger

from Bot.Utils.middlewares import CheckInAdminListMiddleware, CheckInEmployeeListMiddleware
from Bot.Utils.middlewares import CheckInWhiteListMiddleware
from SERVER.server_requests import iiko_webhook, bot, dp

# from Bot.Utils.scheduler import scheduler, load_jobs

app = web.Application()


async def on_startup():
    await bot.set_webhook(f'{config.base_url}{config.path_webhook}')
    bot_logger.info("Webhook for Telegram set up complete")
    bot_logger.info("Bot started")


async def on_shutdown():
    bot_logger.info("Webhook shutdown complete")
    bot_logger.info("Bot shutdown")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()


def main():
    # await load_jobs()
    # scheduler.start()

    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(employee_router)

    dp.update.outer_middleware(CheckInWhiteListMiddleware())
    dp.message.outer_middleware(CheckInWhiteListMiddleware())
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

    app.router.add_post(path=f"{config.path_webhook_iiko}", handler=iiko_webhook)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=config.host_web, port=config.port_web)


if __name__ == "__main__":
    try:
        bot_logger.info("Starting BOT...")
        main()
    except Exception as _ex:
        bot_logger.critical(f'Starting BOT failed with error: {_ex}')
