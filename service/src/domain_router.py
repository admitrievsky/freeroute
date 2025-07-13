import itertools
from collections import deque
from typing import Deque

from config import DomainList, get_config
from domain_lists import match_domain
from ip_route import del_route, add_route
from logger import logger

MAX_LAST_RESOLVED_DOMAINS = 1000
_last_routed_domains: Deque[tuple[str, list[str]]] = deque(
    maxlen=MAX_LAST_RESOLVED_DOMAINS)

iface_name_to_config = {
    config.name: config for config in get_config().networking.tunnels
}


async def route_domain(domain_list: DomainList, domain: str, ips: list[str]):
    _last_routed_domains.append((domain, ips))

    if domain_list is not None:
        if domain_list.name == 'force_default':
            logger.debug(f'Forcing default route to %s for %s', ips, domain)
            await del_route(ips)
            return

        iface_config = iface_name_to_config[domain_list.interface]
        logger.debug(f'Adding route to %s via %s for %s', ips,
                     iface_config.name, domain)
        await add_route(iface_config, ips)
    else:
        logger.debug(f'No preferences for %s. Trying to remove route if any',
                     domain)
        await del_route(ips)


async def re_route_domain(domain: str):
    ips = itertools.chain(
        *(x[1] for x in _last_routed_domains if x[0] == domain)
    )
    ips = list(set(ips))
    if ips:
        logger.debug(f'Re-routing domain %s with ips %s', domain, ips)
        domain_list = await match_domain(domain, None)
        await route_domain(domain_list, domain, ips)
    else:
        logger.debug(f'Domain %s was not routed before. Nothing to reroute',
                     domain)
