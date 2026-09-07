"""Explicit, administrator-only Telegram metadata operations.

These operations deliberately never run during normal bot startup. They modify
Telegram-managed state and can be rate-limited by Telegram.
"""

from collections.abc import Awaitable, Callable

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message

from bot.app.commands import register_commands
from bot.app.core.config import get_settings
from bot.app.profile import configure_profile_descriptions, configure_profile_names


router = Router(name=__name__)

ADMIN_HELP = """Admin commands

/admin_help — show this message
/admin_update_descriptions — update the bot's full and short Telegram descriptions
/admin_update_names — update localized Telegram bot names
/admin_update_commands — update localized Telegram command menus

These commands are intentionally manual. They never run when the bot starts."""


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return (
            message.from_user is not None
            and message.from_user.id in get_settings().admin_telegram_ids
        )


@router.message(Command("admin_help"), IsAdmin())
async def admin_help(message: Message) -> None:
    await message.answer(ADMIN_HELP)


@router.message(Command("admin_update_descriptions"), IsAdmin())
async def admin_update_descriptions(message: Message, bot: Bot) -> None:
    await _run_telegram_update(
        message,
        bot,
        configure_profile_descriptions,
        "Telegram descriptions updated.",
    )


@router.message(Command("admin_update_names"), IsAdmin())
async def admin_update_names(message: Message, bot: Bot) -> None:
    await _run_telegram_update(
        message,
        bot,
        configure_profile_names,
        "Telegram bot names updated.",
    )


@router.message(Command("admin_update_commands"), IsAdmin())
async def admin_update_commands(message: Message, bot: Bot) -> None:
    await _run_telegram_update(
        message,
        bot,
        register_commands,
        "Telegram command menus updated.",
    )


async def _run_telegram_update(
    message: Message,
    bot: Bot,
    operation: Callable[[Bot], Awaitable[None]],
    success_message: str,
) -> None:
    try:
        await operation(bot)
    except TelegramRetryAfter as error:
        await message.answer(
            f"Telegram rate limit. Retry after {error.retry_after} seconds."
        )
    except TelegramAPIError as error:
        await message.answer(f"Telegram API error: {error.message}")
    else:
        await message.answer(success_message)
