from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    telegram_bot_token: SecretStr = Field(alias="TELEGRAM_BOT_TOKEN")
    api_base_url: str = Field(
        default="http://127.0.0.1:8000",
        alias="API_BASE_URL",
    )
    default_timezone: str = Field(
        default="Europe/Moscow",
        alias="DEFAULT_TIMEZONE",
    )
    weekly_reports_enabled: bool = Field(
        default=False,
        alias="WEEKLY_REPORTS_ENABLED",
    )
    admin_telegram_ids_raw: str = Field(
        default="",
        alias="ADMIN_TELEGRAM_IDS",
    )

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def admin_telegram_ids(self) -> frozenset[int]:
        """Telegram user IDs allowed to run one-off bot administration commands."""
        values = [value.strip() for value in self.admin_telegram_ids_raw.split(",")]
        try:
            return frozenset(int(value) for value in values if value)
        except ValueError as error:
            raise ValueError(
                "ADMIN_TELEGRAM_IDS must be a comma-separated list of numeric Telegram IDs"
            ) from error


@lru_cache
def get_settings() -> Settings:
    return Settings()
