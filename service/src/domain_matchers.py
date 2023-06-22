from bisect import bisect, bisect_left

import aiofiles as aiofiles


class DomainMatcher:
    _prefixes: list[str]

    def __init__(self):
        self._prefixes = []

    async def update(self, domain_suffixes):
        self._prefixes = sorted(s[::-1] for s in domain_suffixes)

    def match(self, domain: str) -> bool:
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
