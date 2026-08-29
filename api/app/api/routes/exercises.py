from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import get_db_session
from api.app.schemas.exercise import (
    ExerciseCreateRequest,
    ExerciseResponse,
    ExerciseUpdateRequest,
)
from api.app.schemas.exercise_stats import ExerciseStatsResponse
from api.app.schemas.user import ExternalId, Provider
from api.app.services.exercise import (
    ExerciseNotFoundError,
    archive_exercise,
    clear_exercise_history,
    create_exercise,
    list_exercises,
    permanently_delete_exercise,
    rename_exercise,
)
from api.app.services.exercise_stats import get_exercise_stats
from api.app.services.user import UserBannedError, UserNotFoundError


router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get(
    "/{exercise_id}/stats",
    response_model=ExerciseStatsResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
    },
)
async def get_stats(
    exercise_id: int,
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExerciseStatsResponse:
    try:
        stats = await get_exercise_stats(
            session,
            provider,
            external_id,
            exercise_id,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        ) from error

    return ExerciseStatsResponse.model_validate(stats)


@router.get(
    "",
    response_model=list[ExerciseResponse],
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_exercises(
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ExerciseResponse]:
    try:
        exercises = await list_exercises(session, provider, external_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error

    return [ExerciseResponse.model_validate(exercise) for exercise in exercises]


@router.post(
    "",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def post_exercise(
    payload: ExerciseCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExerciseResponse:
    try:
        exercise = await create_exercise(
            session,
            payload.provider,
            payload.external_id,
            payload.name,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error

    return ExerciseResponse.model_validate(exercise)


@router.patch(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
    },
)
async def patch_exercise(
    exercise_id: int,
    payload: ExerciseUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExerciseResponse:
    try:
        exercise = await rename_exercise(
            session,
            payload.provider,
            payload.external_id,
            exercise_id,
            payload.name,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        ) from error

    return ExerciseResponse.model_validate(exercise)


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
    },
)
async def delete_exercise(
    exercise_id: int,
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    try:
        await archive_exercise(session, provider, external_id, exercise_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{exercise_id}/history",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
    },
)
async def delete_exercise_history(
    exercise_id: int,
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    try:
        await clear_exercise_history(session, provider, external_id, exercise_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise HTTPException(status_code=404, detail="Exercise not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{exercise_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "User is banned"},
        status.HTTP_404_NOT_FOUND: {"description": "User or exercise not found"},
    },
)
async def hard_delete_exercise(
    exercise_id: int,
    provider: Annotated[Provider, Query()],
    external_id: Annotated[ExternalId, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    try:
        await permanently_delete_exercise(
            session, provider, external_id, exercise_id
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise HTTPException(status_code=404, detail="Exercise not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
