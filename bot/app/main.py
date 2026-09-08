import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import RepTrackerApi
from bot.app.core.config import get_settings
from bot.app.handlers import (
    admin_router,
    exercises_router,
    history_router,
    results_router,
    settings_router,
    start_router,
    commands_router,
)
from bot.app.localization import LocalizationMiddleware
from bot.app.notifications import notify_administrators
from bot.app.handlers.weekly_reports import router as weekly_reports_router
from bot.app.protection import MAX_CONCURRENT_UPDATES, PerUserRateLimitMiddleware
from bot.app.workers.weekly_reports import run_worker


async def notify_admins_about_startup(
    bot: Bot,
    administrator_ids: frozenset[int],
) -> None:
    """Notify configured administrators without blocking bot startup."""
    await notify_administrators(bot, administrator_ids, "Repka bot started.")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token.get_secret_value())
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(PerUserRateLimitMiddleware())
    dispatcher.update.outer_middleware(LocalizationMiddleware())
    dispatcher.include_router(admin_router)
    dispatcher.include_router(start_router)
    dispatcher.include_router(commands_router)
    dispatcher.include_router(weekly_reports_router)
    dispatcher.include_router(settings_router)
    dispatcher.include_router(exercises_router)
    dispatcher.include_router(history_router)
    dispatcher.include_router(results_router)

    try:
        async with RepTrackerApi(settings.api_base_url) as api_client:
            await notify_admins_about_startup(bot, settings.admin_telegram_ids)
            worker = (
                asyncio.create_task(run_worker(bot, api_client))
                if settings.weekly_reports_enabled
                else None
            )
            try:
                await dispatcher.start_polling(
                    bot,
                    api_client=api_client,
                    default_timezone=settings.default_timezone,
                    tasks_concurrency_limit=MAX_CONCURRENT_UPDATES,
                )
            finally:
                if worker is not None:
                    worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await worker
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
