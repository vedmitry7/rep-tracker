from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import get_db_session
from api.app.schemas.user import (
    ExternalId,
    Provider,
    UserResolveRequest,
    UserResponse,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
)
from api.app.services.user import (
    UserBannedError,
    UserNotFoundError,
    get_user_settings,
    resolve_user,
    update_user_settings,
)


router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/resolve",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_201_CREATED: {
            "model": UserResponse,
            "description": "User created",
        },
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
    },
)
async def resolve_user_identity(
    payload: UserResolveRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    try:
        result = await resolve_user(
            session=session,
            provider=payload.provider,
            external_id=payload.external_id,
            default_timezone=payload.default_timezone,
            default_language=payload.default_language,
        )
    except UserBannedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned",
        ) from error

    if result.created:
        response.status_code = status.HTTP_201_CREATED

    return UserResponse.model_validate(result.user)


@router.get(
    "/settings",
    response_model=UserSettingsResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def read_user_settings(
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserSettingsResponse:
    try:
        settings = await get_user_settings(session, provider, external_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    return UserSettingsResponse.model_validate(settings, from_attributes=True)


@router.patch(
    "/settings",
    response_model=UserSettingsResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def patch_user_settings(
    payload: UserSettingsUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserSettingsResponse:
    try:
        settings = await update_user_settings(
            session,
            payload.provider,
            payload.external_id,
            timezone=payload.timezone,
            language=payload.language,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    return UserSettingsResponse.model_validate(settings, from_attributes=True)


def _identity_http_error(error: Exception) -> HTTPException:
    if isinstance(error, UserBannedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned",
        )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )
