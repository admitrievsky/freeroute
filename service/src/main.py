import asyncio
import signal

from dns_proxy import (
    DnsProxy
)
from domain_lists import init_external_domain_lists, match_domain


async def on_resolve(domain: str, ip):
    print(f'{domain} resolved to {ip}')
    print(f'List: {match_domain(domain)}')


async def async_main():
    tasks = set()

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
