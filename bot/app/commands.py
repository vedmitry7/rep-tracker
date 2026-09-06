from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.app.texts import get_text


async def register_commands(bot: Bot) -> None:
    """Default English plus Telegram language-specific RU/EN menus."""
    for language_code, catalog in [("", "en"), ("ru", "ru"), ("en", "en")]:
        descriptions = get_text(catalog, "COMMAND_DESCRIPTIONS")
        await bot.set_my_commands(
            [BotCommand(command=command, description=descriptions[command])
             for command in ("menu", "settings", "help")],
            scope=BotCommandScopeDefault(),
            language_code=language_code,
        )
