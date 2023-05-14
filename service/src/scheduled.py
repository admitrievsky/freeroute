import asyncio
import logging

logger = logging.getLogger('freeroute')


def scheduled(interval: float):
    def wrapped(func):
        async def inner(*args, **kwargs):
            while True:
                try:
                    await func(*args, **kwargs)
                except Exception:  # noqa
                    logger.exception(f'Failed to execute scheduled task')
                await asyncio.sleep(interval)

        return inner

    return wrapped
