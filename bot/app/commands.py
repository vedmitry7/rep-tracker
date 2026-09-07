from aiogram import Bot
from aiogram.types import BotCommand


DEFAULT_COMMANDS = [
    BotCommand(command="menu", description="Open menu"),
    BotCommand(command="settings", description="Settings"),
    BotCommand(command="help", description="Help"),
]

RUSSIAN_COMMANDS = [
    BotCommand(command="menu", description="Открыть меню"),
    BotCommand(command="settings", description="Настройки"),
    BotCommand(command="help", description="Помощь"),
]


async def register_commands(bot: Bot) -> None:
    """Register the command menu in Telegram's default, Russian and English UIs."""

    await bot.set_my_commands(DEFAULT_COMMANDS)
    await bot.set_my_commands(RUSSIAN_COMMANDS, language_code="ru")
    await bot.set_my_commands(DEFAULT_COMMANDS, language_code="en")
