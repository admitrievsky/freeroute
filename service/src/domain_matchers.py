import asyncio
import socket
from bisect import bisect, bisect_left
from ipaddress import IPv4Address
from typing import Optional
from weakref import WeakValueDictionary

import aiofiles as aiofiles
import aiohttp
from aiodnsresolver import MemoizedMutex
from aiohttp.abc import AbstractResolver

from logger import logger


class DomainMatcher:
    _prefixes: list[str]

    def __init__(self):
        self._prefixes = []

    async def update(self, domain_suffixes):
        self._prefixes = sorted(s[::-1] for s in domain_suffixes)

    async def match(self, domain: str, ips: Optional[list[IPv4Address]]) -> bool:
        domain = domain[::-1]
        p = bisect(self._prefixes, domain)
        if p == 0:
            return False
        return domain.startswith(self._prefixes[p - 1])

    async def add(self, domain: str):
        domain = domain[::-1]
        p = bisect_left(self._prefixes, domain)
        if p < len(self._prefixes) and self._prefixes[p] == domain:
            return
        self._prefixes.insert(p, domain)

    async def remove(self, domain: str):
        domain = domain[::-1]
        p = bisect_left(self._prefixes, domain)
        if p < len(self._prefixes) and self._prefixes[p] == domain:
            self._prefixes.pop(p)

    def get_all(self):
        return sorted(s[::-1] for s in self._prefixes)


class SerializableDomainMatcher(DomainMatcher):
    _file_name: str

    def __init__(self, file_name: str):
        super().__init__()
        self._file_name = file_name

    async def update(self, domain_suffixes):
        await super().update(domain_suffixes)
        await self.dump()

    async def add(self, domain: str):
        await super().add(domain)
        await self.dump()

    async def remove(self, domain: str):
        await super().remove(domain)
        await self.dump()

    def dump_empty(self):
        assert self._prefixes == []
        with open(self._file_name, 'w') as file:
            pass

    async def dump(self):
        prefixes = '\n'.join(sorted(p[::-1] for p in self._prefixes))
        async with aiofiles.open(self._file_name, 'w') as file:
            await file.write(prefixes)

    async def load(self):
        with open(self._file_name, 'r') as file:
            stripped_lines = (line.strip() for line in file.readlines())
            await super().update(
                line for line in stripped_lines if line
            )


class StaticResolver(AbstractResolver):
    def __init__(self, mapping):
        self._mapping = mapping

    async def resolve(self, host, port=0, family=socket.AF_INET):
        if host not in self._mapping:
            raise aiohttp.ClientError(f"Host {host} not found in static mapping")
        return [{
            'hostname': host,
            'host': self._mapping[host],
            'port': port,
            'family': family,
            'proto': 0,
            'flags': 0,
        }]

    async def close(self):
        pass


class DynamicDomainMatcher(DomainMatcher):
    _timeout: float
    timeout: aiohttp.ClientTimeout
    cache: dict[str, bool] # True if a domain is blocked and needs to be routed through the VPN, False if it is not blocked
    in_progres: WeakValueDictionary
    # TODO: add cache expiration logic
    # TODO: Protected

    def __init__(self, timeout: float = 3):
        super().__init__()
        self._timeout = timeout
        self.timeout = aiohttp.ClientTimeout(total=self._timeout)
        self.cache = {}
        self.in_progress = WeakValueDictionary()

    async def update(self, domain_suffixes):
        pass

    async def add(self, domain: str):
        pass

    async def remove(self, domain: str):
        pass

    async def match(self, domain: str, ips: list[IPv4Address]) -> bool:
        if domain in self.cache:
            return self.cache[domain]

        try:
            memoized_mutex = self.in_progress[domain]
        except KeyError:
            memoized_mutex = MemoizedMutex(
                self.request_and_cache, domain, ips)
            self.in_progress[domain] = memoized_mutex
        else:
            logger.debug(
                'Concurrent request found, waiting for it to complete')

        return await memoized_mutex()

    def get_all(self):
        return []

    async def request_and_cache(self, domain: str, ips: Optional[list[IPv4Address]]):
        if not ips:
            logger.debug(f'No IPs provided for domain {domain}, assuming not blocked')
            return False
        # gather all IPs and make requests to each
        tasks = [request(domain, ip, self.timeout) for ip in ips]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        # if any request returns True, the domain is blocked
        is_blocked = any(results)
        self.cache[domain] = is_blocked
        logger.debug(f'Domain {domain} is {"blocked" if is_blocked else "not blocked"}')
        return is_blocked


async def request(domain: str, ip: IPv4Address, timeout: aiohttp.ClientTimeout) -> bool:
    url = f'https://{domain}'
    resolver = StaticResolver({domain: str(ip)})
    connector = aiohttp.TCPConnector(resolver=resolver)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(url) as response:
                logger.debug(f'Response for {domain}, {ip}: {response.status}')
    except asyncio.exceptions.TimeoutError:
        logger.debug(f'Timeout for {domain}, {ip}')
        return True
    except Exception as e:
        logger.trace(f'Error for {domain}, {ip}: {e}', exc_info=True)
        logger.debug(f'The host responds to {domain} with {ip}, it\'s not blocked, but there was an error: {e}, which could be normal')
    return False
