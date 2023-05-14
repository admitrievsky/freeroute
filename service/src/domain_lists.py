import logging
from typing import Coroutine, Optional, Any, Callable

import aiohttp

from config import ExternalDomainList, get_config, DomainList
from domain_matcher import DomainMatcher
from scheduled import scheduled

logger = logging.getLogger('freeroute')

lists: dict[DomainList, DomainMatcher] = {}


def init_external_domain_lists() -> list[
    Callable[[], Coroutine[Any, Any, Optional[Any]]]]:
    async def update(list_config: ExternalDomainList, matcher: DomainMatcher):
        logger.info(f'Updating list {list_config.name}')
        async with aiohttp.ClientSession() as session:
            async with session.get(list_config.url) as resp:
                assert resp.status == 200
                matcher.update((await resp.text()).splitlines())
                logger.info(f'Updated list {list_config.name}')

    def init() -> list[Callable[[], Coroutine[Any, Any, Optional[Any]]]]:
        result = []
        for list_config in get_config().external_domain_lists:
            matcher = DomainMatcher()
            lists[list_config] = matcher

            @scheduled(list_config.update_interval_hours * 3600)
            async def task():
                await update(list_config, matcher)

            result.append(task)

        return result

    return init()


def match_domain(domain: str) -> Optional[DomainList]:
    return next((list_config for list_config, matcher in lists.items()
                 if matcher.match(domain)), None)
