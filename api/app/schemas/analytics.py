from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from api.app.schemas.user import ExternalId, Provider


EventType = Literal[
    "stats_opened",
    "weekly_report_opened",
    "weekly_delivery_failed",
]


class EventTrackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId
    event_type: EventType


class RetentionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cohort_size: int
    returned_users: int


class AnalyticsSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_days: int
    period_started_at: datetime
    generated_at: datetime
    total_users: int
    new_users: int
    active_users: int
    activated_new_users: int
    result_entries: int
    average_entries_per_active_user: float
    feature_opens: dict[str, int]
    locales: dict[str, int]
    retention: dict[str, RetentionResponse]
    blocked_users: int
    weekly_delivery_failures: int
