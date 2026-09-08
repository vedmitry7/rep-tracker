from unittest.mock import AsyncMock

import pytest
from aiogram.types import User

from bot.app.protection import PerUserRateLimitMiddleware


def user(user_id: int) -> User:
    return User(id=user_id, is_bot=False, first_name="Test")


@pytest.mark.asyncio
async def test_rate_limit_drops_fifth_action_in_two_seconds() -> None:
    clock = iter((0.0, 0.1, 0.2, 0.3, 0.4)).__next__
    middleware = PerUserRateLimitMiddleware(clock=clock)
    handler = AsyncMock()

    for _ in range(5):
        await middleware(handler, object(), {"event_from_user": user(1)})

    assert handler.await_count == 4


@pytest.mark.asyncio
async def test_rate_limit_allows_action_after_window_expires() -> None:
    clock = iter((0.0, 0.1, 0.2, 0.3, 0.4, 2.5)).__next__
    middleware = PerUserRateLimitMiddleware(clock=clock)
    handler = AsyncMock()

    for _ in range(6):
        await middleware(handler, object(), {"event_from_user": user(1)})

    assert handler.await_count == 5


@pytest.mark.asyncio
async def test_rate_limit_tracks_users_with_a_bounded_cache() -> None:
    middleware = PerUserRateLimitMiddleware(max_tracked_users=2)
    handler = AsyncMock()

    for user_id in (1, 2, 3):
        await middleware(handler, object(), {"event_from_user": user(user_id)})

    assert len(middleware._actions) == 2
    assert 1 not in middleware._actions
