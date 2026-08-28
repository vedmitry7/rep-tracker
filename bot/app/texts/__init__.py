"""Small localization interface for the Telegram bot."""

from contextvars import ContextVar, Token
from types import ModuleType
from typing import Any

from bot.app.texts import en, ru


SUPPORTED_LANGUAGES = frozenset({"en", "ru"})
FALLBACK_LANGUAGE = "en"
_catalogs: dict[str, ModuleType] = {"en": en, "ru": ru}
_current_language: ContextVar[str] = ContextVar(
    "telegram_ui_language",
    default="ru",
)


def normalize_language_code(language_code: str | None) -> str:
    if not language_code:
        return FALLBACK_LANGUAGE
    primary = language_code.lower().replace("_", "-").split("-", 1)[0]
    return primary if primary in SUPPORTED_LANGUAGES else FALLBACK_LANGUAGE


def _get_value(language: str | None, key: str) -> Any:
    language = language if language in SUPPORTED_LANGUAGES else FALLBACK_LANGUAGE
    catalog = _catalogs[language]
    return getattr(catalog, key, getattr(en, key))


def get_text(language: str | None, key: str, *args: object, **kwargs: object) -> Any:
    value = _get_value(language, key)
    return value(*args, **kwargs) if callable(value) else value


def set_current_language(language: str | None) -> Token[str]:
    return _current_language.set(normalize_language_code(language))


def reset_current_language(token: Token[str]) -> None:
    _current_language.reset(token)


def current_language() -> str:
    return _current_language.get()


class _LocalizedTexts:
    def __getattr__(self, key: str) -> Any:
        return _get_value(current_language(), key)


texts = _LocalizedTexts()


__all__ = [
    "FALLBACK_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "current_language",
    "get_text",
    "normalize_language_code",
    "reset_current_language",
    "set_current_language",
    "texts",
]
