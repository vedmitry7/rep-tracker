import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from aiogram.exceptions import TelegramRetryAfter

T = TypeVar("T")


async def send_with_rate_limit_retry(send: Callable[[], Awaitable[T]]) -> T:
    """Retry explicit Telegram rate-limit rejections, never ambiguous timeouts."""
    for attempt in range(3):
        try:
            return await send()
        except TelegramRetryAfter as error:
            if attempt == 2:
                raise
            await asyncio.sleep(error.retry_after)
    raise AssertionError("Unreachable")
