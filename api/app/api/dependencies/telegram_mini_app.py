"""Verification of Telegram Mini App initData.

Telegram signs the complete initData query string with the bot token.  The
browser sends the opaque value unchanged; no browser-provided user ID is used
for authentication or ownership checks.
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from api.app.core.config import get_settings
from api.app.core.languages import normalize_default_language


AUTH_HEADER = "X-Telegram-Init-Data"
AUTH_ERROR_DETAIL = "Invalid Telegram Mini App authentication"
MAX_INIT_DATA_LENGTH = 8_192


@dataclass(frozen=True, slots=True)
class TelegramMiniAppIdentity:
    """Server-verified identity carried by a signed Telegram initData value."""

    provider: str
    external_id: str
    language: str


def _authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=AUTH_ERROR_DETAIL,
        headers={"WWW-Authenticate": "TelegramInitData"},
    )


def verify_telegram_init_data(init_data: str, *, now: int | None = None) -> TelegramMiniAppIdentity:
    """Validate initData according to Telegram's Mini App HMAC scheme."""

    if not init_data or len(init_data) > MAX_INIT_DATA_LENGTH:
        raise _authentication_error()

    try:
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    except ValueError as error:
        raise _authentication_error() from error

    values: dict[str, str] = {}
    for key, value in pairs:
        # Duplicate keys make the signed representation ambiguous.
        if not key or key in values:
            raise _authentication_error()
        values[key] = value

    received_hash = values.pop("hash", "")
    auth_date_raw = values.get("auth_date")
    user_raw = values.get("user")
    if not received_hash or auth_date_raw is None or user_raw is None:
        raise _authentication_error()

    settings = get_settings()
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_bot_token.get_secret_value().encode("utf-8"),
        hashlib.sha256,
    ).digest()
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(values.items())
    )
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise _authentication_error()

    try:
        auth_date = int(auth_date_raw)
        user = json.loads(user_raw)
        telegram_id = user["id"]
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise _authentication_error() from error

    if isinstance(telegram_id, bool) or not isinstance(telegram_id, int) or telegram_id <= 0:
        raise _authentication_error()

    current_time = int(time.time()) if now is None else now
    # Small clock skew is tolerated, but values from the future or stale values
    # cannot be replayed indefinitely.
    if auth_date > current_time + 60 or current_time - auth_date > settings.telegram_init_data_max_age_seconds:
        raise _authentication_error()

    return TelegramMiniAppIdentity(
        provider="telegram",
        external_id=str(telegram_id),
        language=normalize_default_language(user.get("language_code")),
    )


async def get_telegram_mini_app_identity(
    init_data: str | None = Header(default=None, alias=AUTH_HEADER),
) -> TelegramMiniAppIdentity:
    return verify_telegram_init_data(init_data or "")
