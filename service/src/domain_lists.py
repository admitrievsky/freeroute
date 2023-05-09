import asyncio
import logging
from typing import Coroutine, Optional

import aiohttp

from config import ExternalDomainList, get_config, DomainList
from domain_matcher import DomainMatcher

logger = logging.getLogger('freeroute')

lists: dict[DomainList, DomainMatcher] = {}


def init_external_domain_lists() -> list[Coroutine]:
    async def update(list_config: ExternalDomainList, matcher: DomainMatcher):
        logger.info(f'Updating list {list_config.name}')
        async with aiohttp.ClientSession() as session:
            async with session.get(list_config.url) as resp:
                assert resp.status == 200
                matcher.update((await resp.text()).splitlines())
                logger.info(f'Updated list {list_config.name}')

    async def update_task(list_config: ExternalDomainList,
                          matcher: DomainMatcher):
        while True:
            try:
                await update(list_config, matcher)
            except Exception:  # noqa
                logger.exception(f'Failed to update list {list_config.name}')
            await asyncio.sleep(list_config.update_interval_hours * 3600)

    def init() -> list[Coroutine]:
        result = []
        for list_config in get_config().external_domain_lists:
            matcher = DomainMatcher()
            lists[list_config] = matcher
            result += [
                update_task(list_config, matcher)
            ]
        return result

    return init()


def match_domain(domain: str) -> Optional[DomainList]:
    return next((list_config for list_config, matcher in lists.items()
                 if matcher.match(domain)), None)
