import logging
from bisect import bisect, bisect_left

import aiofiles as aiofiles

logger = logging.getLogger('freeroute')


class DomainMatcher:
    _prefixes: list[str]

    def __init__(self):
        self._prefixes = []

    def update(self, domain_suffixes):
        self._prefixes = sorted(s[::-1] for s in domain_suffixes)

    def match(self, domain: str) -> bool:
        domain = domain[::-1]
        p = bisect(self._prefixes, domain)
        if p == 0:
            return False
        return domain.startswith(self._prefixes[p - 1])

    def add(self, domain: str):
        domain = domain[::-1]
        p = bisect_left(self._prefixes, domain)
        if p < len(self._prefixes) and self._prefixes[p] == domain:
            return
        self._prefixes.insert(p, domain)


class SerializableDomainMatcher(DomainMatcher):
    _file_name: str
    _dirty: bool = False

    def __init__(self, file_name: str):
        super().__init__()
        self._file_name = file_name

    def update(self, domain_suffixes):
        super().update(domain_suffixes)
        self._dirty = True

    def add(self, domain: str):
        super().add(domain)
        self._dirty = True

    def dump_empty(self):
        assert self._prefixes == []
        with open(self._file_name, 'w') as file:
            pass

    async def dump(self):
        self._dirty = False
        prefixes = '\n'.join(sorted(p[::-1] for p in self._prefixes))
        try:
            with aiofiles.open(self._file_name, 'w') as file:
                await file.write(prefixes)
        except Exception:
            self._dirty = True
            raise

    def load(self):
        with open(self._file_name, 'r') as file:
            stripped_lines = (line.strip() for line in file.readlines())
            super().update(
                line for line in stripped_lines if line
            )

    def is_dirty(self) -> bool:
        return self._dirty
