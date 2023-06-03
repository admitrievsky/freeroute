import asyncio
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class EventType(Enum):
    RESOLVE = 'resolve'


class Event(BaseModel):
    type: EventType


class ResolveEvent(Event):
    remote: str
    domain: str
    ips: list[str]
    domain_list: Optional[str]


class EventLogger:
    _event_logger_queue: asyncio.Queue

    def setup(self):
        self._event_logger_queue = asyncio.Queue()

    def _log_event(self, event: Event):
        self._event_logger_queue.put_nowait(event.json())

    async def get_next_event(self):
        return await self._event_logger_queue.get()

    def log_resolve_event(self, remote: str, domain: str, ips: list[str],
                          domain_list: Optional[str]):
        event = ResolveEvent(
            type=EventType.RESOLVE,
            remote=remote,
            domain=domain,
            ips=ips,
            domain_list=domain_list)
        self._log_event(event)


event_logger = EventLogger()
