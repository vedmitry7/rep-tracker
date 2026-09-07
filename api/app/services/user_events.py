from typing import Literal

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.user import User
from api.app.models.user_event import EVENT_TYPES
from api.app.models.user_event import UserEvent


EventType = Literal[
    "start",
    "exercise_created",
    "result_added",
    "stats_opened",
    "weekly_report_opened",
    "import_used",
    "export_used",
    "weekly_delivery_failed",
]


async def record_user_event(
    session: AsyncSession,
    user: User,
    event_type: EventType,
) -> None:
    """Persist one product event and keep the user's activity timestamp current."""

    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unknown user event: {event_type}")
    session.add(UserEvent(user_id=user.id, event_type=event_type))
    user.last_active_at = func.now()
