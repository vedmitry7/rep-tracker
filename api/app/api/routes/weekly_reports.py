from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from api.app.db.session import get_db_session
from api.app.schemas.user import ExternalId, Provider
from api.app.schemas.weekly_report import (
    MaterializeWeeklyReportsPage,
    WeeklyReportDeliveryResult,
    WeeklyReportLeasePage,
    WeeklyReportLeaseRequest,
    WeeklyReportResponse,
)
from api.app.services.exercise import ExerciseNotFoundError
from api.app.services.user import UserBannedError, UserNotFoundError
from api.app.services.weekly_card import render_card
from api.app.services.weekly_report import (
    complete_delivery,
    get_card_data,
    lease_reports,
    materialize_reports,
    owned_report,
)

router = APIRouter(tags=["weekly reports"])
Session = Annotated[AsyncSession, Depends(get_db_session)]


def identity_error(error):
    return HTTPException(403 if isinstance(error, UserBannedError) else 404,
                         "User, exercise or report unavailable")


@router.get("/exercises/{exercise_id}/weekly-card", response_class=Response,
            responses={200: {"content": {"image/png": {}}}})
async def weekly_card(exercise_id: int, provider: Provider, external_id: ExternalId,
                      session: Session, report_id: str | None = None):
    try:
        data, language = await get_card_data(session, provider, external_id, exercise_id, report_id)
    except (UserNotFoundError, UserBannedError, ExerciseNotFoundError) as error:
        raise identity_error(error) from error
    if data is None:
        raise HTTPException(404, "No complete-week data")
    png = await run_in_threadpool(render_card, data, language)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/weekly-reports/materialize", response_model=MaterializeWeeklyReportsPage)
async def materialize(
    session: Session,
    after_id: Annotated[int, Query(ge=0)] = 0,
):
    return await materialize_reports(
        session,
        after_id=after_id,
    )


@router.post("/weekly-reports/lease", response_model=WeeklyReportLeasePage)
async def lease(payload: WeeklyReportLeaseRequest, session: Session):
    return {"reports": await lease_reports(session, payload.worker_id, payload.limit)}


@router.get("/weekly-reports/{report_id}", response_model=WeeklyReportResponse)
async def get_report(report_id: str, provider: Provider, external_id: ExternalId, session: Session):
    try:
        async with session.begin():
            report = await owned_report(session, provider, external_id, report_id)
            if report is None:
                raise HTTPException(404, "Report not found")
            return dict(id=report.id, **report.payload)
    except (UserNotFoundError, UserBannedError) as error:
        raise identity_error(error) from error


@router.post("/weekly-reports/{report_id}/delivery", status_code=204)
async def delivery(report_id: str, payload: WeeklyReportDeliveryResult, session: Session):
    completed = await complete_delivery(
        session,
        report_id,
        payload.lock_token,
        payload.status,
        error=payload.error,
        retry_after_seconds=payload.retry_after_seconds,
    )
    if not completed:
        raise HTTPException(409, "Weekly report lease is no longer active")
    return Response(status_code=204)
