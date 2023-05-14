import asyncio
import logging
import re

from config import get_config, InterfaceConfig
from scheduled import scheduled

logger = logging.getLogger('freeroute')

cache: dict[InterfaceConfig, set[str]] = {}


async def exec_command(*args):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f'Executing command: {" ".join(args)}')
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if stderr:
        logger.info(
            f'Command `{" ".join(args)}` failed with error: {stderr.decode()}')
    return stdout.decode()


async def ip_route(*args):
    command = get_config().ip_route_command.split(' ')
    return await exec_command(*command, *args)


async def add_route(interface: InterfaceConfig, ips: list[str]):
    dirty = False
    for ip in ips:
        if ip in cache[interface]:
            continue
        dirty = True
        cache[interface].add(ip)
        await ip_route('add', ip, 'via', interface.gateway_ip)
    if dirty:
        await flush_cache()
    else:
        logger.debug(f'Route for {ips} already exists. Nothing to add')


async def del_route(ips: list[str]):
    dirty = False
    for ip in ips:
        for interface, cache_ips in cache.items():
            if ip in cache_ips:
                break
        else:
            continue
        dirty = True
        cache[interface].remove(ip)
        await ip_route('del', ip)
    if dirty:
        await flush_cache()
    else:
        logger.debug(f'No route for {ips}. Nothing to remove')


async def get_routes():
    return await ip_route('show')


async def flush_cache():
    await ip_route('flush', 'cache')


@scheduled(60)
async def sync_ip_route_cache():
    logger.info('Syncing ip route cache')
    global cache
    gateway_ips_to_iface_configs = {
        config.gateway_ip: config for config in get_config().networking.tunnels
    }
    cache = {
        config: set() for config in gateway_ips_to_iface_configs.values()
    }

    actual_routes_by_gateway = {}

    for route in (await get_routes()).splitlines():
        values = re.match(r'(\d+\.\d+\.\d+\.\d+).*via (\d+\.\d+\.\d+\.\d+)',
                          route)
        if values is None:
            continue
        ip, gateway_ip = values.groups()
        actual_routes_by_gateway.setdefault(gateway_ip, set()).add(ip)

    for gateway_ip, ips in actual_routes_by_gateway.items():
        iface_config = gateway_ips_to_iface_configs.get(gateway_ip)
        if iface_config is None:
            continue
        cache[iface_config] = ips
