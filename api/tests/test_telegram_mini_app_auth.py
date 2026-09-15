import hashlib
import hmac
import json
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from api.app.api.dependencies import telegram_mini_app


BOT_TOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
NOW = 1_700_000_000


def signed_init_data(**values: object) -> str:
    values.setdefault("auth_date", str(NOW))
    values.setdefault("user", json.dumps({"id": 123, "language_code": "ru"}))
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


@pytest.fixture(autouse=True)
def mini_app_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        telegram_bot_token=SecretStr(BOT_TOKEN),
        telegram_init_data_max_age_seconds=86_400,
    )
    monkeypatch.setattr(telegram_mini_app, "get_settings", lambda: settings)


def test_signed_init_data_returns_server_verified_telegram_identity():
    identity = telegram_mini_app.verify_telegram_init_data(signed_init_data(), now=NOW)

    assert identity.provider == "telegram"
    assert identity.external_id == "123"
    assert identity.language == "ru"


@pytest.mark.parametrize(
    "init_data",
    [
        "",
        f"{signed_init_data()}&extra=tampered",
        f"{signed_init_data()}&user={json.dumps({'id': 123})}",
    ],
)
def test_rejects_unsigned_or_ambiguous_init_data(init_data: str):
    with pytest.raises(HTTPException) as error:
        telegram_mini_app.verify_telegram_init_data(init_data, now=NOW)

    assert error.value.status_code == 401


def test_rejects_stale_init_data():
    with pytest.raises(HTTPException) as error:
        telegram_mini_app.verify_telegram_init_data(
            signed_init_data(auth_date=str(NOW - 86_401)), now=NOW
        )

    assert error.value.status_code == 401
