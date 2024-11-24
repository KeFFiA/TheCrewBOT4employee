import ssl

from aiohttp import web

import config
from Bot.Utils.logging_settings import servers_logger
from SERVER.server_requests import iiko_webhook, index, handle_validation, privacy, iiko_card_webhook
from path import CERT_PATH, KEY_PATH

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

app = web.Application()


def start_server():
    try:
        app.router.add_get(path='/privacy', handler=privacy)
        app.router.add_post(path=f"{config.path_webhook_iiko}", handler=iiko_webhook)
        app.router.add_post(path='/webhook/iiko-card/staff', handler=iiko_card_webhook)
        app.router.add_get(path='/', handler=index)
        app.router.add_get(path='/.well-known/acme-challenge/{token}', handler=handle_validation)
    except Exception as _ex:
        servers_logger.exception(f"Adding router error: {_ex}")
    try:
        web.run_app(app, host=config.host_web, port=config.port_web, ssl_context=ssl_context)
        # web.run_app(app, host=config.host_web, port=config.port_web)
        servers_logger.info("Server started successfully")
    except Exception as _ex:
        servers_logger.exception(f"Starting server error: {_ex}")



