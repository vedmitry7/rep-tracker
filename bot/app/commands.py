from aiogram import Bot
from aiogram.types import BotCommand

from bot.app.texts import available_locales, get_catalog


def commands_for(language: str) -> list[BotCommand]:
    return [
        BotCommand(command=command, description=description)
        for command, description in get_catalog(language).BOT_COMMANDS.items()
    ]


async def register_commands(bot: Bot) -> None:
    """Register a default menu and a menu for every bot-local locale."""

    await bot.set_my_commands(commands_for("en"))
    for locale in available_locales():
        await bot.set_my_commands(
            commands_for(locale.code),
            language_code=locale.code,
        )
