from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from bot.app.api.client import ApiError, RepTrackerApi
from bot.app.texts import (
    normalize_language_code,
    reset_current_language,
    set_current_language,
)


class UserLanguageStore:
    """Small process-local cache; the backend remains authoritative."""

    def __init__(self) -> None:
        self._languages: dict[int, str] = {}

    def get(self, telegram_user_id: int) -> str | None:
        return self._languages.get(telegram_user_id)

    def set(self, telegram_user_id: int, language: str) -> None:
        self._languages[telegram_user_id] = normalize_language_code(language)

    def clear(self) -> None:
        self._languages.clear()


user_languages = UserLanguageStore()


class LocalizationMiddleware(BaseMiddleware):
    def __init__(self, store: UserLanguageStore = user_languages) -> None:
        self._store = store

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        language = self._telegram_default(user)
        if isinstance(user, User):
            cached = self._store.get(user.id)
            if cached is not None:
                language = cached
            else:
                api_client = data.get("api_client")
                if isinstance(api_client, RepTrackerApi):
                    try:
                        settings = await api_client.get_user_settings(user.id)
                    except ApiError:
                        pass
                    else:
                        language = settings.language
                        self._store.set(user.id, language)

        token = set_current_language(language)
        try:
            return await handler(event, data)
        finally:
            reset_current_language(token)

    @staticmethod
    def _telegram_default(user: object) -> str:
        language_code = user.language_code if isinstance(user, User) else None
        return normalize_language_code(language_code)
