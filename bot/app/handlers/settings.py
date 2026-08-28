from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.app.api.client import ApiError, InvalidRequestError, RepTrackerApi
from bot.app.handlers.common import answer_api_error
from bot.app.keyboards.exercises import add_exercise_keyboard, exercises_list_keyboard
from bot.app.keyboards.settings import (
    LanguageChoice,
    SettingsAction,
    SettingsActionValue,
    TimezoneChoice,
    TimezonePageChoice,
    language_choices_keyboard,
    settings_back_keyboard,
    settings_keyboard,
    timezone_choices_keyboard,
)
from bot.app.localization import user_languages
from bot.app.states.settings import ChangeTimezone
from bot.app.texts import (
    current_language,
    reset_current_language,
    set_current_language,
    texts,
)
from bot.app.timezones import DEFAULT_TIMEZONE_PAGE, format_timezone


router = Router(name=__name__)


@router.callback_query(SettingsAction.filter(F.action == SettingsActionValue.OPEN))
async def show_settings(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    try:
        settings = await api_client.get_user_settings(callback.from_user.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    language = getattr(settings, "language", "ru")
    user_languages.set(callback.from_user.id, language)
    token = set_current_language(language)
    try:
        await callback.answer()
        await _render(
            callback,
            texts.settings(
                format_timezone(settings.timezone, language),
                _language_name(language),
            ),
            settings_keyboard(),
        )
    finally:
        reset_current_language(token)


@router.callback_query(
    SettingsAction.filter(F.action == SettingsActionValue.CHANGE_LANGUAGE)
)
async def choose_language(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await _render(callback, texts.CHOOSE_LANGUAGE, language_choices_keyboard())


@router.callback_query(LanguageChoice.filter())
async def set_language(
    callback: CallbackQuery,
    callback_data: LanguageChoice,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    try:
        settings = await api_client.update_user_language(
            callback.from_user.id,
            callback_data.language,
        )
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await state.clear()
    user_languages.set(callback.from_user.id, settings.language)
    token = set_current_language(settings.language)
    try:
        await callback.answer(texts.LANGUAGE_CHANGED)
        await _render(
            callback,
            texts.language_changed(_language_name(settings.language)),
            settings_back_keyboard(),
        )
    finally:
        reset_current_language(token)


@router.callback_query(
    SettingsAction.filter(F.action == SettingsActionValue.CHANGE_TIMEZONE)
)
async def choose_timezone(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await _render(
        callback,
        texts.CHOOSE_TIMEZONE,
        timezone_choices_keyboard(DEFAULT_TIMEZONE_PAGE),
    )


@router.callback_query(TimezonePageChoice.filter())
async def paginate_timezones(
    callback: CallbackQuery,
    callback_data: TimezonePageChoice,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.answer()
    await _render(
        callback,
        texts.CHOOSE_TIMEZONE,
        timezone_choices_keyboard(callback_data.page),
    )


@router.callback_query(
    SettingsAction.filter(F.action == SettingsActionValue.OTHER_TIMEZONE)
)
async def request_other_timezone(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ChangeTimezone.entering_timezone)
    await callback.answer()
    await _render(
        callback,
        texts.ENTER_TIMEZONE,
        settings_back_keyboard(),
    )


@router.callback_query(TimezoneChoice.filter())
async def set_popular_timezone(
    callback: CallbackQuery,
    callback_data: TimezoneChoice,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await _update_timezone(
        callback,
        state,
        api_client,
        callback.from_user.id,
        callback_data.timezone,
    )


@router.message(ChangeTimezone.entering_timezone)
async def set_custom_timezone(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    if message.from_user is None:
        return
    timezone = (message.text or "").strip()
    if not timezone:
        await message.answer(texts.ENTER_TIMEZONE_REQUIRED)
        return
    await _update_timezone(
        message,
        state,
        api_client,
        message.from_user.id,
        timezone,
    )


@router.callback_query(SettingsAction.filter(F.action == SettingsActionValue.HOME))
async def settings_home(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    try:
        exercises = await api_client.list_exercises(callback.from_user.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    await callback.answer()
    if exercises:
        await _render(
            callback,
            texts.EXERCISES_TITLE,
            exercises_list_keyboard(exercises),
        )
    else:
        await _render(callback, texts.NO_EXERCISES, add_exercise_keyboard())


async def _update_timezone(
    event: Message | CallbackQuery,
    state: FSMContext,
    api_client: RepTrackerApi,
    telegram_user_id: int,
    timezone: str,
) -> None:
    try:
        settings = await api_client.update_user_timezone(telegram_user_id, timezone)
    except InvalidRequestError:
        text = texts.INVALID_TIMEZONE
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        else:
            await event.answer(text)
        return
    except ApiError as error:
        await answer_api_error(event, error)
        return

    await state.clear()
    language = getattr(settings, "language", current_language())
    user_languages.set(telegram_user_id, language)
    token = set_current_language(language)
    try:
        if isinstance(event, CallbackQuery):
            await event.answer(texts.TIMEZONE_CHANGED)
        await _render(
            event,
            texts.settings(
                format_timezone(settings.timezone, language),
                _language_name(language),
            ),
            settings_keyboard(),
        )
    finally:
        reset_current_language(token)


async def _render(
    event: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    if isinstance(event, CallbackQuery):
        if isinstance(event.message, Message):
            await event.message.edit_text(text, reply_markup=reply_markup)
        return
    await event.answer(text, reply_markup=reply_markup)


def _language_name(language: str) -> str:
    return texts.LANGUAGE_RUSSIAN if language == "ru" else texts.LANGUAGE_ENGLISH
    language_choices_keyboard,
