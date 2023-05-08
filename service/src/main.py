import asyncio
import signal

from dns_proxy import (
    DnsProxy
)


async def async_main():
    start = DnsProxy(resolved_callback=lambda domain, ip: print(
        f'{domain} resolved to {ip}'))
    proxy_task = await start()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, proxy_task.cancel)
    loop.add_signal_handler(signal.SIGTERM, proxy_task.cancel)

    try:
        await proxy_task
    except asyncio.CancelledError:
        pass


if __name__ == '__main__':
    asyncio.run(async_main())
