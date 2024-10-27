from aiohttp import web

import config
from SERVER.server_requests import iiko_webhook

app = web.Application()

async def hello_world(request):
    return web.Response(text="Hello World!")

def start_server():
    app.router.add_post(path=f"{config.path_webhook_iiko}", handler=iiko_webhook)
    app.router.add_get(path='/', handler=hello_world)
    web.run_app(app, host=config.host_web, port=config.port_web)


