from typing import Coroutine, Optional, Any, Callable

import aiohttp

from config import ExternalDomainList, get_config, DomainList
from domain_matchers import DomainMatcher, SerializableDomainMatcher
from logger import logger
from scheduled import scheduled

lists: dict[DomainList, DomainMatcher] = {}


def init_external_domain_lists() -> list[
    Callable[[], Coroutine[Any, Any, Optional[Any]]]]:
    async def update(list_config: ExternalDomainList, matcher: DomainMatcher):
        logger.info(f'Updating list {list_config.name}')
        async with aiohttp.ClientSession() as session:
            async with session.get(list_config.url) as resp:
                assert resp.status == 200
                await matcher.update((await resp.text()).splitlines())
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


async def init_manual_domain_lists():
    for list_config in get_config().manual_domain_lists:
        matcher = SerializableDomainMatcher(f'list_{list_config.name}.txt')
        try:
            logger.info(f'Loading manual list {list_config.name}')
            await matcher.load()
        except FileNotFoundError as e:
            logger.info(f'File {e.filename} not found, creating new one')
            matcher.dump_empty()
        lists[list_config] = matcher


def match_domain(domain: str) -> Optional[DomainList]:
    return next((list_config for list_config, matcher in lists.items()
                 if matcher.match(domain)), None)


def get_manual_domain_lists() -> dict[str, DomainList]:
    return {list_config.name: list_config for list_config in
            get_config().manual_domain_lists}


def get_domain_matcher(list_config: DomainList) -> DomainMatcher:
    return lists[list_config]
