"""Small, process-local guards for Telegram update abuse."""

from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User


USER_ACTION_LIMIT = 4
USER_ACTION_WINDOW_SECONDS = 2.0
MAX_TRACKED_USERS = 10_000
MAX_CONCURRENT_UPDATES = 20


class PerUserRateLimitMiddleware(BaseMiddleware):
    """Drop bursts before they reach localization, handlers, or the API."""

    def __init__(
        self,
        *,
        action_limit: int = USER_ACTION_LIMIT,
        window_seconds: float = USER_ACTION_WINDOW_SECONDS,
        max_tracked_users: int = MAX_TRACKED_USERS,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._action_limit = action_limit
        self._window_seconds = window_seconds
        self._max_tracked_users = max_tracked_users
        self._clock = clock
        self._actions: OrderedDict[int, deque[float]] = OrderedDict()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not isinstance(user, User) or not self._allow(user.id):
            return None
        return await handler(event, data)

    def _allow(self, user_id: int) -> bool:
        now = self._clock()
        cutoff = now - self._window_seconds
        actions = self._actions.get(user_id)
        if actions is None:
            actions = deque()
            self._actions[user_id] = actions
            while len(self._actions) > self._max_tracked_users:
                self._actions.popitem(last=False)
        else:
            self._actions.move_to_end(user_id)

        while actions and actions[0] <= cutoff:
            actions.popleft()
        if len(actions) >= self._action_limit:
            return False

        actions.append(now)
        return True
