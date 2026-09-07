"""Durable, rate-limited Telegram delivery worker for weekly reports."""
import asyncio
import logging
from uuid import uuid4

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from bot.app.api.client import RepTrackerApi
from bot.app.core.config import get_settings
from bot.app.services.weekly_report import report_keyboard, split_summary


logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 30
MESSAGE_INTERVAL_SECONDS = 1
LEASE_BATCH_SIZE = 10


async def _record_delivery_failure(api_client, telegram_user_id: int) -> None:
    track_event = getattr(api_client, "track_event_safely", None)
    if track_event is not None:
        await track_event(telegram_user_id, "weekly_delivery_failed")


async def materialize_all(api_client) -> None:
    cursor = 0
    while True:
        page = await api_client.materialize_weekly_reports(cursor)
        cursor = page["next_cursor"]
        if cursor is None:
            return


async def mark_retry(api_client, report: dict, error: Exception, retry_after_seconds: int | None = None) -> None:
    try:
        await api_client.complete_weekly_delivery(
            report["id"],
            report["lock_token"],
            "retry",
            error=f"{type(error).__name__}: {error}"[:1000],
            retry_after_seconds=retry_after_seconds,
        )
    except Exception:
        # The lease will expire and become eligible again. That is intentional:
        # Telegram cannot provide exactly-once acknowledgement.
        logger.exception("Weekly delivery retry acknowledgement failed: %s", report["id"])


async def deliver_leased_reports(bot, api_client, worker_id: str) -> int:
    page = await api_client.lease_weekly_reports(worker_id, LEASE_BATCH_SIZE)
    reports = page["reports"]
    for report in reports:
        try:
            messages = split_summary(report)
            for index, text in enumerate(messages):
                await bot.send_message(
                    chat_id=int(report["external_id"]),
                    text=text,
                    reply_markup=report_keyboard(report) if index == len(messages) - 1 else None,
                    parse_mode=None,
                )
                await asyncio.sleep(MESSAGE_INTERVAL_SECONDS)
        except TelegramRetryAfter as error:
            logger.info("Telegram rate limit for weekly report %s: retry in %s seconds",
                        report["id"], error.retry_after)
            await mark_retry(api_client, report, error, retry_after_seconds=int(error.retry_after))
            await _record_delivery_failure(api_client, int(report["external_id"]))
        except TelegramForbiddenError as error:
            logger.info("Telegram user blocked the bot: %s", report["external_id"])
            await _record_delivery_failure(api_client, int(report["external_id"]))
            try:
                mark_user_blocked = getattr(api_client, "mark_user_blocked", None)
                if mark_user_blocked is None:
                    raise RuntimeError("API client cannot mark a blocked user")
                await mark_user_blocked(int(report["external_id"]))
                await api_client.complete_weekly_delivery(
                    report["id"], report["lock_token"], "failed", error=str(error)[:1000]
                )
            except Exception:
                logger.exception("Could not record blocked Telegram user: %s", report["id"])
        except Exception as error:
            logger.exception("Weekly report delivery failed: %s", report["id"])
            await mark_retry(api_client, report, error)
            await _record_delivery_failure(api_client, int(report["external_id"]))
        else:
            try:
                await api_client.complete_weekly_delivery(
                    report["id"], report["lock_token"], "sent"
                )
            except Exception:
                # Do not claim success locally: the lease expiry makes this an
                # at-least-once retry if the API acknowledgement was lost.
                logger.exception("Weekly delivery acknowledgement failed: %s", report["id"])
    return len(reports)


async def run_worker(bot, api_client) -> None:
    worker_id = str(uuid4())
    while True:
        try:
            await materialize_all(api_client)
            while await deliver_leased_reports(bot, api_client, worker_id):
                pass
        except Exception:
            logger.exception("Weekly report worker tick failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    if not settings.weekly_reports_enabled:
        logger.info("Weekly report worker is disabled by WEEKLY_REPORTS_ENABLED")
        return
    bot = Bot(token=settings.telegram_bot_token.get_secret_value())
    try:
        async with RepTrackerApi(settings.api_base_url) as api_client:
            await run_worker(bot, api_client)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
