from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_validator,
    model_validator,
)

from api.app.core.dates import DEFAULT_TIMEZONE, validate_timezone_name
from api.app.core.languages import DEFAULT_LANGUAGE, normalize_default_language


Provider = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]
ExternalId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
TimezoneName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
    AfterValidator(validate_timezone_name),
]
Language = Literal["en", "ru"]


class UserResolveRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "provider": "telegram",
                "external_id": "123456789",
                "default_timezone": DEFAULT_TIMEZONE,
                "default_language": "ru",
            }
        },
    )

    provider: Provider
    external_id: ExternalId
    default_timezone: TimezoneName = DEFAULT_TIMEZONE
    default_language: str = DEFAULT_LANGUAGE

    @field_validator("default_language", mode="before")
    @classmethod
    def fallback_unknown_default_language(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return normalize_default_language(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "created_at": "2026-08-27T12:00:00Z",
                "is_banned": False,
                "timezone": "Europe/Moscow",
                "language": "ru",
            }
        },
    )

    id: int
    created_at: datetime
    is_banned: bool
    timezone: str
    language: Language


class UserSettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId
    timezone: TimezoneName | None = None
    language: Language | None = None

    @model_validator(mode="after")
    def require_a_setting(self) -> Self:
        if self.timezone is None and self.language is None:
            raise ValueError("At least one of timezone or language is required")
        return self


class UserSettingsResponse(BaseModel):
    timezone: str
    today: date
    language: Language
