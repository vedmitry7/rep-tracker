from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import get_db_session
from api.app.schemas.exercise_entry import (
    ExerciseEntryCreateRequest,
    ExerciseEntryResponse,
    ExerciseEntryUpdateRequest,
)
from api.app.schemas.exercise_history import ExerciseHistoryDayResponse
from api.app.schemas.user import ExternalId, Provider
from api.app.services.exercise import ExerciseNotFoundError
from api.app.services.exercise_entry import (
    ExerciseArchivedError,
    ExerciseDateInFutureError,
    ExerciseEntryNotFoundError,
    create_exercise_entry,
    delete_exercise_entry,
    list_exercise_entries,
    update_exercise_entry,
)
from api.app.services.exercise_history import list_exercise_history_days
from api.app.services.user import UserBannedError, UserNotFoundError


router = APIRouter(tags=["exercise entries"])

DEFAULT_ENTRY_LIMIT = 50
MAX_ENTRY_LIMIT = 100


@router.get(
    "/exercises/{exercise_id}/history-days",
    response_model=list[ExerciseHistoryDayResponse],
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
    },
)
async def get_exercise_history_days(
    exercise_id: int,
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_ENTRY_LIMIT)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ExerciseHistoryDayResponse]:
    try:
        days = await list_exercise_history_days(
            session,
            provider,
            external_id,
            exercise_id,
            limit,
            offset,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found_http_error("Exercise not found") from error

    return [ExerciseHistoryDayResponse.model_validate(day) for day in days]


@router.post(
    "/exercise-entries",
    response_model=ExerciseEntryResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
        status.HTTP_409_CONFLICT: {"description": "Exercise is archived"},
    },
)
async def post_exercise_entry(
    payload: ExerciseEntryCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExerciseEntryResponse:
    try:
        entry = await create_exercise_entry(
            session,
            payload.provider,
            payload.external_id,
            payload.exercise_id,
            payload.reps,
            payload.performed_on,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found_http_error("Exercise not found") from error
    except ExerciseArchivedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise is archived",
        ) from error
    except ExerciseDateInFutureError as error:
        raise _future_date_http_error() from error

    return ExerciseEntryResponse.model_validate(entry)


@router.get(
    "/exercises/{exercise_id}/entries",
    response_model=list[ExerciseEntryResponse],
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
    },
)
async def get_exercise_entries(
    exercise_id: int,
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_ENTRY_LIMIT)] = DEFAULT_ENTRY_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ExerciseEntryResponse]:
    try:
        entries = await list_exercise_entries(
            session,
            provider,
            external_id,
            exercise_id,
            from_date,
            to_date,
            limit,
            offset,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found_http_error("Exercise not found") from error

    return [ExerciseEntryResponse.model_validate(entry) for entry in entries]


@router.patch(
    "/exercise-entries/{entry_id}",
    response_model=ExerciseEntryResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or entry not found"},
    },
)
async def patch_exercise_entry(
    entry_id: int,
    payload: ExerciseEntryUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExerciseEntryResponse:
    changes = payload.model_dump(
        exclude={"provider", "external_id"},
        exclude_unset=True,
    )
    try:
        entry = await update_exercise_entry(
            session,
            payload.provider,
            payload.external_id,
            entry_id,
            changes,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseEntryNotFoundError as error:
        raise _not_found_http_error("Exercise entry not found") from error
    except ExerciseDateInFutureError as error:
        raise _future_date_http_error() from error

    return ExerciseEntryResponse.model_validate(entry)


@router.delete(
    "/exercise-entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or entry not found"},
    },
)
async def remove_exercise_entry(
    entry_id: int,
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    try:
        await delete_exercise_entry(
            session,
            provider,
            external_id,
            entry_id,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseEntryNotFoundError as error:
        raise _not_found_http_error("Exercise entry not found") from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _identity_http_error(error: Exception) -> HTTPException:
    if isinstance(error, UserBannedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned",
        )
    return _not_found_http_error("User not found")


def _not_found_http_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _future_date_http_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="performed_on cannot be in the future",
    )
