from datetime import datetime, timezone

from aiogram import Bot

from bot.app.api.client import RepTrackerApi


async def refund_support_payment(
    bot: Bot,
    api_client: RepTrackerApi,
    telegram_user_id: int,
    telegram_payment_charge_id: str,
) -> None:
    """Refund a known Stars charge; intentionally not exposed as a user action."""
    await bot.refund_star_payment(
        user_id=telegram_user_id,
        telegram_payment_charge_id=telegram_payment_charge_id,
    )
    await api_client.mark_support_payment_refunded(
        telegram_payment_charge_id,
        datetime.now(timezone.utc),
    )
