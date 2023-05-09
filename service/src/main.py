import asyncio
import logging
import signal
import sys

from aiodnsresolver import IPv4AddressExpiresAt

from config import get_config
from dns_proxy import (
    DnsProxy
)
from domain_lists import init_external_domain_lists, match_domain
from ip_route import add_route, del_route, init_ip_route_cache

iface_name_to_config = {
    config.name: config for config in get_config().networking.tunnels
}

logger = logging.getLogger('freeroute')

for logger_name, level in {'freeroute': 'DEBUG',
                           'dnsrewriteproxy': 'ERROR'}.items():
    logging.getLogger(logger_name).setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    logging.getLogger(logger_name).addHandler(handler)


async def on_resolve(domain: str, ips: list[IPv4AddressExpiresAt]):
    domain_list = match_domain(domain)
    ips_str = [str(ip) for ip in ips]
    if domain_list is not None:
        iface_config = iface_name_to_config[domain_list.interface]
        logger.debug(f'Adding route to %s via %s', ips_str, iface_config.name)
        await add_route(iface_config, ips_str)
    else:
        logger.debug(f'No route for %s. Removing it', domain)
        await del_route(ips_str)


async def async_main():
    tasks = set()

    await init_ip_route_cache()

    start = DnsProxy(resolved_callback=on_resolve)
    proxy_task = await start()
    tasks.add(proxy_task)

    external_domain_list_tasks = init_external_domain_lists()
    tasks.add(*external_domain_list_tasks)
    for task in external_domain_list_tasks:
        asyncio.create_task(task)

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, proxy_task.cancel)
    loop.add_signal_handler(signal.SIGTERM, proxy_task.cancel)

    try:
        await proxy_task
    except asyncio.CancelledError:
        pass


if __name__ == '__main__':
    asyncio.run(async_main())
