from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.app.schemas.user import ExternalId, Language, Provider


class WeekTotal(BaseModel):
    start: date
    total: int


class WeeklyBestDay(BaseModel):
    date: date
    reps: int


class ExerciseWeek(BaseModel):
    exercise_id: int
    name: str
    total: int
    previous: int | None
    delta: int | None
    percent: float | None
    active_days: int
    best_day: WeeklyBestDay | None
    history: list[WeekTotal]


class WeeklyReportResponse(BaseModel):
    id: str
    week_start: date
    week_end: date
    language: Language
    exercises: list[ExerciseWeek]


class MaterializeWeeklyReportsPage(BaseModel):
    next_cursor: int | None


class WeeklyReportLeaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: Annotated[str, Field(min_length=1, max_length=64)]
    limit: Annotated[int, Field(ge=1, le=10)] = 10


class LeasedWeeklyReport(WeeklyReportResponse):
    external_id: ExternalId
    lock_token: UUID


class WeeklyReportLeasePage(BaseModel):
    reports: list[LeasedWeeklyReport]


class WeeklyReportDeliveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lock_token: UUID
    status: Literal["sent", "retry"]
    retry_after_seconds: Annotated[int | None, Field(ge=1, le=86400)] = None
    error: Annotated[str | None, Field(max_length=1000)] = None
