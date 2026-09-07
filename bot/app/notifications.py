"""Best-effort administrator notifications for bot lifecycle events."""

import logging
from collections.abc import Iterable

from aiogram import Bot
from aiogram.types import User

from bot.app.api.client import ApiError, RepTrackerApi


logger = logging.getLogger(__name__)


async def notify_administrators(
    bot: Bot,
    administrator_ids: Iterable[int],
    text: str,
) -> None:
    """Send a message to every administrator without blocking user flows."""
    for administrator_id in administrator_ids:
        try:
            await bot.send_message(administrator_id, text)
        except Exception:
            logger.exception("Could not notify administrator %s", administrator_id)


async def notify_new_user_registration(
    bot: Bot,
    administrator_ids: Iterable[int],
    api_client: RepTrackerApi,
    user: User,
    language: str,
) -> None:
    """Notify administrators about a newly created bot user."""
    try:
        users_today = (await api_client.get_analytics_summary(1)).new_users
    except ApiError:
        logger.warning("Could not load today's new-user count")
        users_today = "unavailable"

    username = f"@{user.username}" if user.username else "not set"
    await notify_administrators(
        bot,
        administrator_ids,
        "New user registered\n"
        f"Name: {user.full_name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n"
        f"Language: {language}\n"
        f"Users today: {users_today}",
    )
