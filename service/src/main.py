import asyncio
import signal

from aiodnsresolver import IPv4AddressExpiresAt

from config import get_config
from dns_proxy import (
    DnsProxy
)
from domain_lists import init_external_domain_lists, match_domain, \
    init_manual_domain_lists
from event_logger import event_logger
from ip_route import add_route, sync_ip_route_cache, del_route
from logger import init_logging, logger
from web_server import setup_web_server, event_source_handler

init_logging()

iface_name_to_config = {
    config.name: config for config in get_config().networking.tunnels
}


async def on_resolve(addr: str, domain: str, ips: list[IPv4AddressExpiresAt]):
    domain_list = match_domain(domain)
    ips_str = [str(ip) for ip in ips]

    event_logger.log_resolve_event(addr[0], domain, ips_str,
                                   domain_list.name if domain_list else None)

    if domain_list is not None:
        if domain_list.name == 'force_default':
            logger.debug(f'Forcing default route to %s for %s', ips_str, domain)
            await del_route(ips_str)
            return

        iface_config = iface_name_to_config[domain_list.interface]
        logger.debug(f'Adding route to %s via %s for %s', ips_str,
                     iface_config.name, domain)
        await add_route(iface_config, ips_str)
    else:
        logger.debug(f'No route for %s. Doing nothing', domain)


async def async_main():
    tasks = set()

    start = DnsProxy(resolved_callback=on_resolve)
    proxy_task = await start()
    tasks.add(proxy_task)

    await init_manual_domain_lists()

    external_domain_list_tasks = init_external_domain_lists()
    for task in external_domain_list_tasks:
        tasks.add(
            asyncio.create_task(task()))

    tasks.add(
        asyncio.create_task(sync_ip_route_cache()))

    tasks.add(
        asyncio.create_task(event_source_handler.event_log_listener_task()))
    event_logger.setup()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, proxy_task.cancel)
    loop.add_signal_handler(signal.SIGTERM, proxy_task.cancel)

    await setup_web_server()

    try:
        await proxy_task
    except asyncio.CancelledError:
        pass


if __name__ == '__main__':
    asyncio.run(async_main())
