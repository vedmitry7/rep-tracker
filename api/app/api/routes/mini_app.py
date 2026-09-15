"""Public, Telegram-authenticated API for the Repka Mini App.

The legacy routes remain available only inside the Docker network for the bot.
This router deliberately has a separate prefix so Caddy can expose only these
routes to the Internet.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.api.dependencies.telegram_mini_app import (
    TelegramMiniAppIdentity,
    get_telegram_mini_app_identity,
)
from api.app.db.session import get_db_session
from api.app.schemas.exercise import (
    ExerciseResponse,
    MiniAppExerciseCreateRequest,
    MiniAppExerciseUpdateRequest,
    MiniAppExerciseWeeklyReportUpdateRequest,
)
from api.app.schemas.exercise_entry import (
    ExerciseEntryResponse,
    MiniAppExerciseEntryCreateRequest,
    MiniAppExerciseEntryUpdateRequest,
)
from api.app.schemas.exercise_history import ExerciseHistoryDayResponse
from api.app.schemas.exercise_stats import ExerciseStatsResponse
from api.app.schemas.user import (
    MiniAppUserResolveRequest,
    MiniAppUserSettingsUpdateRequest,
    UserResponse,
    UserSettingsResponse,
)
from api.app.services.exercise import (
    DuplicateExerciseNameError,
    ExerciseNotFoundError,
    archive_exercise,
    clear_exercise_history,
    create_exercise,
    list_exercises,
    permanently_delete_exercise,
    rename_exercise,
    set_weekly_report_enabled,
)
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
from api.app.services.exercise_stats import get_exercise_stats
from api.app.services.user import (
    UserBannedError,
    UserNotFoundError,
    get_user_settings,
    resolve_user,
    update_user_settings,
)


router = APIRouter(
    prefix="/mini-app",
    tags=["Telegram Mini App"],
)

Identity = Annotated[TelegramMiniAppIdentity, Depends(get_telegram_mini_app_identity)]
Session = Annotated[AsyncSession, Depends(get_db_session)]

DEFAULT_ENTRY_LIMIT = 50
MAX_ENTRY_LIMIT = 100


@router.post("/users/resolve", response_model=UserResponse)
async def resolve_mini_app_user(
    payload: MiniAppUserResolveRequest,
    response: Response,
    identity: Identity,
    session: Session,
) -> UserResponse:
    try:
        result = await resolve_user(
            session,
            identity.provider,
            identity.external_id,
            default_timezone=payload.default_timezone,
            default_language=identity.language,
        )
    except UserBannedError as error:
        raise HTTPException(status_code=403, detail="User is banned") from error
    if result.created:
        response.status_code = status.HTTP_201_CREATED
    return UserResponse.model_validate(result.user)


@router.get("/users/settings", response_model=UserSettingsResponse)
async def read_mini_app_settings(identity: Identity, session: Session) -> UserSettingsResponse:
    try:
        settings = await get_user_settings(session, identity.provider, identity.external_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    return UserSettingsResponse.model_validate(settings, from_attributes=True)


@router.patch("/users/settings", response_model=UserSettingsResponse)
async def patch_mini_app_settings(
    payload: MiniAppUserSettingsUpdateRequest, identity: Identity, session: Session
) -> UserSettingsResponse:
    try:
        settings = await update_user_settings(
            session,
            identity.provider,
            identity.external_id,
            timezone=payload.timezone,
            language=payload.language,
        )
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    return UserSettingsResponse.model_validate(settings, from_attributes=True)


@router.get("/exercises", response_model=list[ExerciseResponse])
async def get_mini_app_exercises(identity: Identity, session: Session) -> list[ExerciseResponse]:
    try:
        exercises = await list_exercises(session, identity.provider, identity.external_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    return [ExerciseResponse.model_validate(exercise) for exercise in exercises]


@router.post("/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def post_mini_app_exercise(
    payload: MiniAppExerciseCreateRequest, identity: Identity, session: Session
) -> ExerciseResponse:
    try:
        exercise = await create_exercise(session, identity.provider, identity.external_id, payload.name)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except DuplicateExerciseNameError as error:
        raise HTTPException(status_code=409, detail="An active exercise with this name already exists") from error
    return ExerciseResponse.model_validate(exercise)


@router.patch("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def patch_mini_app_exercise(
    exercise_id: int, payload: MiniAppExerciseUpdateRequest, identity: Identity, session: Session
) -> ExerciseResponse:
    try:
        exercise = await rename_exercise(session, identity.provider, identity.external_id, exercise_id, payload.name)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    except DuplicateExerciseNameError as error:
        raise HTTPException(status_code=409, detail="An active exercise with this name already exists") from error
    return ExerciseResponse.model_validate(exercise)


@router.patch("/exercises/{exercise_id}/weekly-report", response_model=ExerciseResponse)
async def patch_mini_app_weekly_report(
    exercise_id: int, payload: MiniAppExerciseWeeklyReportUpdateRequest, identity: Identity, session: Session
) -> ExerciseResponse:
    try:
        exercise = await set_weekly_report_enabled(session, identity.provider, identity.external_id, exercise_id, payload.weekly_report_enabled)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    return ExerciseResponse.model_validate(exercise)


@router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mini_app_exercise(exercise_id: int, identity: Identity, session: Session) -> Response:
    try:
        await archive_exercise(session, identity.provider, identity.external_id, exercise_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/exercises/{exercise_id}/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mini_app_exercise_history(exercise_id: int, identity: Identity, session: Session) -> Response:
    try:
        await clear_exercise_history(session, identity.provider, identity.external_id, exercise_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/exercises/{exercise_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_mini_app_exercise(exercise_id: int, identity: Identity, session: Session) -> Response:
    try:
        await permanently_delete_exercise(session, identity.provider, identity.external_id, exercise_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/exercises/{exercise_id}/stats", response_model=ExerciseStatsResponse)
async def get_mini_app_stats(exercise_id: int, identity: Identity, session: Session) -> ExerciseStatsResponse:
    try:
        stats = await get_exercise_stats(session, identity.provider, identity.external_id, exercise_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    return ExerciseStatsResponse.model_validate(stats)


@router.get("/exercises/{exercise_id}/history-days", response_model=list[ExerciseHistoryDayResponse])
async def get_mini_app_history(
    exercise_id: int, identity: Identity, session: Session,
    limit: Annotated[int, Query(ge=1, le=MAX_ENTRY_LIMIT)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ExerciseHistoryDayResponse]:
    try:
        days = await list_exercise_history_days(session, identity.provider, identity.external_id, exercise_id, limit, offset)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    return [ExerciseHistoryDayResponse.model_validate(day) for day in days]


@router.post("/exercise-entries", response_model=ExerciseEntryResponse, status_code=status.HTTP_201_CREATED)
async def post_mini_app_entry(
    payload: MiniAppExerciseEntryCreateRequest, identity: Identity, session: Session
) -> ExerciseEntryResponse:
    try:
        entry = await create_exercise_entry(session, identity.provider, identity.external_id, payload.exercise_id, payload.reps, payload.performed_on)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    except ExerciseArchivedError as error:
        raise HTTPException(status_code=409, detail="Exercise is archived") from error
    except ExerciseDateInFutureError as error:
        raise HTTPException(status_code=422, detail="performed_on cannot be in the future") from error
    return ExerciseEntryResponse.model_validate(entry)


@router.get("/exercises/{exercise_id}/entries", response_model=list[ExerciseEntryResponse])
async def get_mini_app_entries(
    exercise_id: int, identity: Identity, session: Session,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_ENTRY_LIMIT)] = DEFAULT_ENTRY_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ExerciseEntryResponse]:
    try:
        entries = await list_exercise_entries(session, identity.provider, identity.external_id, exercise_id, from_date, to_date, limit, offset)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseNotFoundError as error:
        raise _not_found("Exercise not found") from error
    return [ExerciseEntryResponse.model_validate(entry) for entry in entries]


@router.patch("/exercise-entries/{entry_id}", response_model=ExerciseEntryResponse)
async def patch_mini_app_entry(
    entry_id: int, payload: MiniAppExerciseEntryUpdateRequest, identity: Identity, session: Session
) -> ExerciseEntryResponse:
    try:
        entry = await update_exercise_entry(session, identity.provider, identity.external_id, entry_id, payload.model_dump(exclude_unset=True))
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseEntryNotFoundError as error:
        raise _not_found("Exercise entry not found") from error
    except ExerciseDateInFutureError as error:
        raise HTTPException(status_code=422, detail="performed_on cannot be in the future") from error
    return ExerciseEntryResponse.model_validate(entry)


@router.delete("/exercise-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mini_app_entry(entry_id: int, identity: Identity, session: Session) -> Response:
    try:
        await delete_exercise_entry(session, identity.provider, identity.external_id, entry_id)
    except (UserNotFoundError, UserBannedError) as error:
        raise _identity_http_error(error) from error
    except ExerciseEntryNotFoundError as error:
        raise _not_found("Exercise entry not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _identity_http_error(error: Exception) -> HTTPException:
    if isinstance(error, UserBannedError):
        return HTTPException(status_code=403, detail="User is banned")
    return _not_found("User not found")


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=404, detail=detail)
