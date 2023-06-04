import asyncio

from aiohttp import web
from aiohttp.web_request import BaseRequest
from aiohttp_sse import sse_response

from config import get_config
from event_logger import event_logger
from logger import logger


class EventSourceHandler:
    log_listeners: set

    def __init__(self):
        self.log_listeners = set()

    async def event_source_handler(self, request: BaseRequest):
        async with sse_response(request) as resp:
            queue = asyncio.Queue()
            self.log_listeners.add(queue)

            try:
                while not resp.task.done():
                    data = await queue.get()
                    await resp.send(data)
            except ConnectionResetError:
                logger.info('[log_event_source] Connection reset by client: %s',
                            request.remote)
            finally:
                self.log_listeners.remove(queue)

    async def event_log_listener_task(self):
        while True:
            event = await event_logger.get_next_event()
            for queue in self.log_listeners:
                await queue.put(event)


event_source_handler = EventSourceHandler()


async def domain_list_handler(request: BaseRequest):
    return web.json_response([l.name for l in get_config().manual_domain_lists])


async def setup_web_server():
    app = web.Application()
    app.router.add_route('GET', '/api/event-log',
                         event_source_handler.event_source_handler)
    app.router.add_route('GET', '/api/domain-lists', domain_list_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=get_config().api_port)
    await site.start()
