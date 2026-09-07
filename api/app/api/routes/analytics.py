from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import get_db_session
from api.app.schemas.analytics import AnalyticsSummaryResponse, EventTrackRequest
from api.app.services.analytics import get_analytics_summary
from api.app.services.user import (
    UserBannedError,
    UserNotFoundError,
    get_allowed_user_by_identity,
    mark_user_blocked,
)
from api.app.services.user_events import record_user_event


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_summary(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: Annotated[int, Query()] = 7,
) -> AnalyticsSummaryResponse:
    try:
        async with session.begin():
            summary = await get_analytics_summary(session, period_days=days)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return AnalyticsSummaryResponse.model_validate(summary)


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
async def post_event(
    payload: EventTrackRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    try:
        async with session.begin():
            user = await get_allowed_user_by_identity(
                session, payload.provider, payload.external_id
            )
            await record_user_event(session, user, payload.event_type)
    except UserBannedError as error:
        raise HTTPException(status_code=403, detail="User is banned") from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail="User not found") from error


@router.post("/blocked", status_code=status.HTTP_204_NO_CONTENT)
async def post_blocked_user(
    provider: Annotated[str, Query()],
    external_id: Annotated[str, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await mark_user_blocked(session, provider, external_id)
