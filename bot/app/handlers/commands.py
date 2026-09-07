from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.app.api.client import RepTrackerApi
from bot.app.handlers.settings import send_settings_message
from bot.app.handlers.start import send_menu_message
from bot.app.texts import texts


router = Router(name=__name__)


@router.message(Command("menu"))
async def menu(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
    default_timezone: str,
    bot: Bot | None = None,
) -> None:
    await state.clear()
    await send_menu_message(message, api_client, default_timezone, bot=bot)


@router.message(Command("settings"))
async def settings(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    await send_settings_message(message, api_client)


@router.message(Command("help"))
async def help_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.HELP)
