SUPPORTED_LANGUAGES = frozenset({"en", "ru"})
DEFAULT_LANGUAGE = "en"


def normalize_default_language(value: str | None) -> str:
    """Return a supported locale for a newly created user."""
    if value in SUPPORTED_LANGUAGES:
        return value
    return DEFAULT_LANGUAGE
