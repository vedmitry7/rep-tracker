import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import RepTrackerApi
from bot.app.core.config import get_settings
from bot.app.handlers import (
    exercises_router,
    history_router,
    results_router,
    settings_router,
    start_router,
    commands_router,
)
from bot.app.localization import LocalizationMiddleware
from bot.app.handlers.weekly_reports import router as weekly_reports_router
from bot.app.workers.weekly_reports import run_worker


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token.get_secret_value())
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(LocalizationMiddleware())
    dispatcher.include_router(start_router)
    dispatcher.include_router(commands_router)
    dispatcher.include_router(weekly_reports_router)
    dispatcher.include_router(settings_router)
    dispatcher.include_router(exercises_router)
    dispatcher.include_router(history_router)
    dispatcher.include_router(results_router)

    try:
        async with RepTrackerApi(settings.api_base_url) as api_client:
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
