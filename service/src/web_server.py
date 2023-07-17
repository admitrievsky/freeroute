import asyncio
import os

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp_sse import sse_response

from config import get_config
from domain_lists import get_manual_domain_lists, get_domain_matcher
from domain_matchers import DomainMatcher
from domain_router import re_route_domain
from event_logger import event_logger
from logger import logger


class EventSourceHandler:
    log_listeners: set

    def __init__(self):
        self.log_listeners = set()

    async def event_source_handler(self, request: Request):
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


async def domain_list_handler(request: Request):
    return web.json_response(list(get_manual_domain_lists().keys()))


def get_matcher_by_name(name: str) -> DomainMatcher:
    domain_list = get_manual_domain_lists().get(name)
    if domain_list is None:
        raise web.HTTPNotFound()
    return get_domain_matcher(domain_list)


async def get_domain_list_handler(request: Request):
    domain_list_name = request.match_info['domain_list']
    domain_matcher = get_matcher_by_name(domain_list_name)
    return web.json_response(domain_matcher.get_all())


async def add_domain_handler(request: Request):
    domain_list_name = request.match_info['domain_list']
    domain_matcher = get_matcher_by_name(domain_list_name)
    data = await request.json()
    await domain_matcher.add(data['domain'])
    await re_route_domain(data['domain'])
    return web.json_response('ok')


async def delete_domain_handler(request: Request):
    domain_list_name = request.match_info['domain_list']
    domain_matcher = get_matcher_by_name(domain_list_name)
    data = await request.json()
    await domain_matcher.remove(data['domain'])
    await re_route_domain(data['domain'])
    return web.json_response('ok')


async def setup_web_server():
    app = web.Application()
    app.router.add_route('GET', '/api/event-log',
                         event_source_handler.event_source_handler)

    app.router.add_route('GET', '/api/domain-lists', domain_list_handler)
    app.router.add_route('GET', '/api/domain-lists/{domain_list}',
                         get_domain_list_handler)
    app.router.add_route('POST', '/api/domain-lists/{domain_list}',
                         add_domain_handler)
    app.router.add_route('DELETE', '/api/domain-lists/{domain_list}',
                         delete_domain_handler)
    for try_static in ['service/static', 'ui/build']:
        if os.path.isdir(try_static):
            app.router.add_route('GET', '/', lambda _: web.FileResponse(
                os.path.join(try_static, 'index.html')))
            app.router.add_static('/', try_static, follow_symlinks=True)
            break

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=get_config().api_port)
    await site.start()
