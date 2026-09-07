"""Bot-local catalog manager.

Every module next to this file is a complete Telegram UI locale. The bot discovers
them at startup, so adding a language does not require editing routing or settings
code.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from functools import cache
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Any


FALLBACK_LANGUAGE = "en"


@dataclass(frozen=True)
class Locale:
    code: str
    name: str
    button: str


def _public_keys(catalog: ModuleType) -> set[str]:
    return {key for key in vars(catalog) if not key.startswith("_")}


@cache
def _catalogs() -> dict[str, ModuleType]:
    catalogs: dict[str, ModuleType] = {}
    for module_info in iter_modules(__path__):
        if module_info.name.startswith("_"):
            continue
        catalog = import_module(f"{__name__}.{module_info.name}")
        code = getattr(catalog, "LANGUAGE_CODE", None)
        if not isinstance(code, str) or code != module_info.name:
            raise RuntimeError(f"Locale {module_info.name!r} must define matching LANGUAGE_CODE")
        catalogs[code] = catalog

    if FALLBACK_LANGUAGE not in catalogs:
        raise RuntimeError(f"Missing fallback locale: {FALLBACK_LANGUAGE}")

    reference_keys = _public_keys(catalogs[FALLBACK_LANGUAGE])
    for code, catalog in catalogs.items():
        difference = _public_keys(catalog) ^ reference_keys
        if difference:
            raise RuntimeError(
                f"Locale {code!r} does not match {FALLBACK_LANGUAGE!r}: "
                f"{', '.join(sorted(difference))}"
            )
    return catalogs


SUPPORTED_LANGUAGES = frozenset(_catalogs())


def normalize_language_code(language_code: str | None) -> str:
    if not language_code:
        return FALLBACK_LANGUAGE
    primary = language_code.lower().replace("_", "-").split("-", 1)[0]
    return primary if primary in SUPPORTED_LANGUAGES else FALLBACK_LANGUAGE


def get_catalog(language: str | None) -> ModuleType:
    return _catalogs()[normalize_language_code(language)]


def available_locales() -> tuple[Locale, ...]:
    return tuple(
        Locale(code, catalog.LANGUAGE_NAME, catalog.LANGUAGE_BUTTON)
        for code, catalog in _catalogs().items()
    )


def locale_name(language: str | None) -> str:
    return get_catalog(language).LANGUAGE_NAME


# Backwards-compatible aliases for direct catalog inspection.
en = get_catalog("en")
ru = get_catalog("ru")
_current_language: ContextVar[str] = ContextVar(
    "telegram_ui_language",
    default="ru",
)


def _get_value(language: str | None, key: str) -> Any:
    catalog = get_catalog(language)
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
    "Locale",
    "SUPPORTED_LANGUAGES",
    "available_locales",
    "current_language",
    "get_catalog",
    "get_text",
    "locale_name",
    "normalize_language_code",
    "reset_current_language",
    "set_current_language",
    "texts",
]
