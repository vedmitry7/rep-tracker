from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core.dates import (
    DEFAULT_TIMEZONE,
    get_user_today,
    validate_timezone_name,
)
from api.app.core.languages import DEFAULT_LANGUAGE, normalize_default_language
from api.app.models import User, UserIdentity


UNIQUE_VIOLATION_SQLSTATE = "23505"


class UserBannedError(Exception):
    """Raised when an external identity belongs to a banned user."""


class UserNotFoundError(Exception):
    """Raised when an external identity does not belong to a user."""


@dataclass(frozen=True, slots=True)
class ResolveUserResult:
    user: User
    created: bool


@dataclass(frozen=True, slots=True)
class UserSettings:
    timezone: str
    today: date
    language: str


async def find_user_by_identity(
    session: AsyncSession,
    provider: str,
    external_id: str,
) -> User | None:
    statement = (
        select(User)
        .join(UserIdentity)
        .where(
            UserIdentity.provider == provider,
            UserIdentity.external_id == external_id,
        )
    )
    return await session.scalar(statement)


def ensure_user_is_allowed(user: User) -> None:
    if user.is_banned:
        raise UserBannedError


async def get_allowed_user_by_identity(
    session: AsyncSession,
    provider: str,
    external_id: str,
) -> User:
    user = await find_user_by_identity(session, provider, external_id)
    if user is None:
        raise UserNotFoundError

    ensure_user_is_allowed(user)
    return user


def _is_unique_violation(error: IntegrityError) -> bool:
    candidate: BaseException | None = error.orig
    seen: set[int] = set()

    while candidate is not None and id(candidate) not in seen:
        seen.add(id(candidate))
        if getattr(candidate, "sqlstate", None) == UNIQUE_VIOLATION_SQLSTATE:
            return True
        candidate = candidate.__cause__ or candidate.__context__

    return False


async def resolve_user(
    session: AsyncSession,
    provider: str,
    external_id: str,
    default_timezone: str = DEFAULT_TIMEZONE,
    default_language: str = DEFAULT_LANGUAGE,
) -> ResolveUserResult:
    validate_timezone_name(default_timezone)
    default_language = normalize_default_language(default_language)
    try:
        async with session.begin():
            user = await find_user_by_identity(session, provider, external_id)
            if user is not None:
                ensure_user_is_allowed(user)
                return ResolveUserResult(user=user, created=False)

            user = User(timezone=default_timezone, language=default_language)
            user.identities.append(
                UserIdentity(provider=provider, external_id=external_id)
            )
            session.add(user)
            await session.flush()

            return ResolveUserResult(user=user, created=True)
    except IntegrityError as error:
        if not _is_unique_violation(error):
            raise

        # A concurrent request committed the same identity first. The failed
        # transaction has rolled back both the identity and its temporary user.
        async with session.begin():
            user = await find_user_by_identity(session, provider, external_id)
            if user is None:
                raise error

            ensure_user_is_allowed(user)
            return ResolveUserResult(user=user, created=False)


async def get_user_settings(
    session: AsyncSession,
    provider: str,
    external_id: str,
) -> UserSettings:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        return UserSettings(
            timezone=user.timezone,
            today=get_user_today(user.timezone),
            language=user.language,
        )


async def update_user_settings(
    session: AsyncSession,
    provider: str,
    external_id: str,
    *,
    timezone: str | None = None,
    language: str | None = None,
) -> UserSettings:
    if timezone is not None:
        validate_timezone_name(timezone)
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        if timezone is not None:
            user.timezone = timezone
        if language is not None:
            user.language = language
        await session.flush()
        return UserSettings(
            timezone=user.timezone,
            today=get_user_today(user.timezone),
            language=user.language,
        )
