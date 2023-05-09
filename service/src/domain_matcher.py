from bisect import bisect, bisect_left


class DomainMatcher:
    __prefixes: list[str]

    def __init__(self):
        self.__prefixes = []

    def update(self, domain_suffixes):
        self.__prefixes = sorted(s[::-1] for s in domain_suffixes)

    def match(self, domain: str) -> bool:
        domain = domain[::-1]
        p = bisect(self.__prefixes, domain)
        if p == 0:
            return False
        return domain.startswith(self.__prefixes[p - 1])

    def add(self, domain: str):
        domain = domain[::-1]
        p = bisect_left(self.__prefixes, domain)
        if p < len(self.__prefixes) and self.__prefixes[p] == domain:
            return
        self.__prefixes.insert(p, domain)
