from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.app.api.client import RepTrackerApi
from bot.app.handlers.settings import render_settings
from bot.app.texts import texts

router = Router(name="commands")


@router.message(Command("settings"))
async def settings_command(message: Message, state: FSMContext, api_client: RepTrackerApi):
    await render_settings(message, state, api_client)


@router.message(Command("help"))
async def help_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(texts.HELP_TEXT)
