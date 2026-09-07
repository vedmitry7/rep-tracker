from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.app.api.client import ApiError, RepTrackerApi, UserResolution
from bot.app.core.config import get_settings
from bot.app.handlers.common import answer_api_error
from bot.app.keyboards.exercises import (
    add_exercise_keyboard,
    exercises_list_keyboard,
)
from bot.app.localization import user_languages
from bot.app.notifications import notify_new_user_registration
from bot.app.texts import (
    normalize_language_code,
    reset_current_language,
    set_current_language,
    texts,
)


router = Router(name=__name__)


@router.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
    default_timezone: str,
    bot: Bot | None = None,
) -> None:
    await state.clear()
    await send_menu_message(
        message,
        api_client,
        default_timezone,
        welcome_new_user=True,
        bot=bot,
    )


async def send_menu_message(
    message: Message,
    api_client: RepTrackerApi,
    default_timezone: str,
    *,
    welcome_new_user: bool = False,
    bot: Bot | None = None,
) -> UserResolution | None:
    if message.from_user is None:
        return None

    try:
        default_language = normalize_language_code(
            getattr(message.from_user, "language_code", None)
        )
        resolution = await api_client.resolve_user(
            message.from_user.id,
            default_timezone,
            default_language,
        )
        exercises = await api_client.list_exercises(message.from_user.id)
    except ApiError as error:
        await answer_api_error(message, error)
        return None

    language = getattr(resolution, "language", default_language)
    user_languages.set(message.from_user.id, language)
    token = set_current_language(language)
    try:
        if exercises:
            await message.answer(
                texts.EXERCISES_TITLE,
                reply_markup=exercises_list_keyboard(exercises),
            )
        elif welcome_new_user and resolution.created:
            await message.answer(
                texts.WELCOME,
                reply_markup=add_exercise_keyboard(first_exercise=True),
            )
        else:
            await message.answer(
                texts.NO_EXERCISES,
                reply_markup=add_exercise_keyboard(),
            )
    finally:
        reset_current_language(token)

    if resolution.created and bot is not None:
        await notify_new_user_registration(
            bot,
            get_settings().admin_telegram_ids,
            api_client,
            message.from_user,
            resolution.language,
        )

    return resolution
