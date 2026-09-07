import json
from datetime import datetime
from io import BytesIO

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, Message

from bot.app.api.client import (
    ApiError,
    Exercise,
    ImportPreview,
    InvalidRequestError,
    RepTrackerApi,
)
from bot.app.handlers.common import (
    answer_api_error,
    edit_or_answer,
    edit_stored_or_answer,
)
from bot.app.keyboards.exercises import (
    ExerciseDetailActionValue,
    add_exercise_keyboard,
    exercise_management_selection_keyboard,
    exercises_list_keyboard,
)
from bot.app.keyboards.settings import (
    ExportAction,
    ExportActionValue,
    ExportToggle,
    ImportAction,
    ImportActionValue,
    LanguageChoice,
    SettingsAction,
    SettingsActionValue,
    TimezoneChoice,
    TimezonePageChoice,
    exercise_management_keyboard,
    export_selection_keyboard,
    import_confirmation_keyboard,
    import_strategy_keyboard,
    language_choices_keyboard,
    settings_back_keyboard,
    settings_keyboard,
    timezone_choices_keyboard,
)
from bot.app.localization import user_languages
from bot.app.services.exercise_format import format_number
from bot.app.states.settings import ChangeTimezone, ExportData, ImportData
from bot.app.texts import (
    current_language,
    locale_name,
    reset_current_language,
    set_current_language,
    texts,
)
from bot.app.timezones import DEFAULT_TIMEZONE_PAGE, format_timezone


router = Router(name=__name__)
MAX_IMPORT_FILE_SIZE = 1024 * 1024


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
                locale_name(language),
            ),
            settings_keyboard(),
        )
    finally:
        reset_current_language(token)


async def send_settings_message(
    message: Message,
    api_client: RepTrackerApi,
) -> None:
    """Send the settings screen as a new message for the /settings command."""

    if message.from_user is None:
        return
    try:
        settings = await api_client.get_user_settings(message.from_user.id)
    except ApiError as error:
        await answer_api_error(message, error)
        return
    language = getattr(settings, "language", "ru")
    user_languages.set(message.from_user.id, language)
    token = set_current_language(language)
    try:
        await message.answer(
            texts.settings(
                format_timezone(settings.timezone, language),
                locale_name(language),
            ),
            reply_markup=settings_keyboard(),
        )
    finally:
        reset_current_language(token)


@router.callback_query(
    SettingsAction.filter(F.action == SettingsActionValue.IMPORT_DATA)
)
async def request_import_file(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ImportData.waiting_for_file)
    if isinstance(callback.message, Message):
        await state.update_data(
            ui_chat_id=callback.message.chat.id,
            ui_message_id=callback.message.message_id,
        )
    await callback.answer()
    await _render(
        callback,
        texts.IMPORT_SEND_FILE,
        settings_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(
    SettingsAction.filter(F.action == SettingsActionValue.EXPORT_DATA)
)
async def request_export(
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
    if not exercises:
        await _render(callback, texts.EXPORT_NO_EXERCISES, settings_back_keyboard())
        return

    selected_ids = {exercise.id for exercise in exercises}
    await state.set_state(ExportData.selecting_exercises)
    await state.update_data(
        export_exercises=[exercise.model_dump() for exercise in exercises],
        export_selected_ids=list(selected_ids),
    )
    await _render(
        callback,
        texts.export_selection(selected=len(selected_ids), total=len(exercises)),
        export_selection_keyboard(exercises, selected_ids),
    )


@router.callback_query(ExportData.selecting_exercises, ExportToggle.filter())
async def toggle_export_exercise(
    callback: CallbackQuery,
    callback_data: ExportToggle,
    state: FSMContext,
) -> None:
    export_state = await _export_state(state)
    if export_state is None:
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return
    exercises, selected_ids = export_state
    exercise_ids = {exercise.id for exercise in exercises}
    if callback_data.exercise_id not in exercise_ids:
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return

    if callback_data.exercise_id in selected_ids:
        selected_ids.remove(callback_data.exercise_id)
    else:
        selected_ids.add(callback_data.exercise_id)
    await state.update_data(export_selected_ids=list(selected_ids))
    await callback.answer()
    await _render(
        callback,
        texts.export_selection(selected=len(selected_ids), total=len(exercises)),
        export_selection_keyboard(exercises, selected_ids),
    )


@router.callback_query(
    ExportData.selecting_exercises,
    ExportAction.filter(F.action == ExportActionValue.APPLY),
)
async def export_selected_exercises(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    export_state = await _export_state(state)
    if export_state is None:
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return
    exercises, selected_ids = export_state
    selected_exercises = [
        exercise for exercise in exercises if exercise.id in selected_ids
    ]
    if not selected_exercises:
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return

    try:
        document = await api_client.export_data(
            callback.from_user.id,
            [exercise.id for exercise in selected_exercises],
        )
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    content = json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")
    if len(content) > MAX_IMPORT_FILE_SIZE:
        await callback.answer(texts.EXPORT_FILE_TOO_LARGE, show_alert=True)
        return
    if not isinstance(callback.message, Message):
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return

    await callback.message.answer_document(
        BufferedInputFile(content, filename=_export_filename())
    )
    await state.clear()
    await callback.answer()
    await _render(
        callback,
        texts.export_completed(
            exercises=format_number(len(selected_exercises)),
            entries=format_number(_export_entries_count(document)),
        ),
        settings_back_keyboard(),
    )


@router.message(ImportData.waiting_for_file)
async def receive_import_file(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    if message.from_user is None:
        return
    document = message.document
    if document is None or not (document.file_name or "").lower().endswith(".json"):
        await message.answer(texts.IMPORT_JSON_ONLY)
        return
    if document.file_size is not None and document.file_size > MAX_IMPORT_FILE_SIZE:
        await message.answer(texts.IMPORT_FILE_TOO_LARGE)
        return

    buffer = BytesIO()
    await message.bot.download(document.file_id, destination=buffer)
    if buffer.tell() > MAX_IMPORT_FILE_SIZE:
        await message.answer(texts.IMPORT_FILE_TOO_LARGE)
        return
    try:
        payload = json.loads(buffer.getvalue().decode("utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("top-level JSON value must be an object")
        preview = await api_client.preview_import(message.from_user.id, payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, InvalidRequestError):
        await message.answer(texts.IMPORT_INVALID_FILE)
        return
    except ApiError as error:
        await answer_api_error(message, error)
        return

    await state.update_data(
        import_document=payload,
        import_preview=preview.model_dump(mode="json"),
    )
    data = await state.get_data()
    chat_id = data.get("ui_chat_id")
    message_id = data.get("ui_message_id")
    stored_chat_id = chat_id if isinstance(chat_id, int) else None
    stored_message_id = message_id if isinstance(message_id, int) else None
    if preview.existing_exercises:
        await state.set_state(ImportData.waiting_for_strategy)
        await edit_stored_or_answer(
            message,
            _import_preview_text(preview),
            import_strategy_keyboard(),
            chat_id=stored_chat_id,
            message_id=stored_message_id,
        )
        return

    await state.set_state(ImportData.waiting_for_confirmation)
    await edit_stored_or_answer(
        message,
        _new_exercises_import_text(preview),
        import_confirmation_keyboard("merge"),
        chat_id=stored_chat_id,
        message_id=stored_message_id,
    )


@router.callback_query(
    ImportData.waiting_for_strategy,
    ImportAction.filter(
        F.action.in_({ImportActionValue.MERGE, ImportActionValue.REPLACE})
    ),
)
async def choose_import_strategy(
    callback: CallbackQuery,
    callback_data: ImportAction,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    try:
        preview = ImportPreview.model_validate(data["import_preview"])
    except (KeyError, ValueError):
        await state.clear()
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return
    strategy = callback_data.action.value
    await state.set_state(ImportData.waiting_for_confirmation)
    await callback.answer()
    await _render(
        callback,
        texts.import_confirmation(
            strategy,
            format_number(preview.entries_count),
            len(preview.existing_exercises),
        ),
        import_confirmation_keyboard(strategy),
    )


@router.callback_query(
    ImportData.waiting_for_confirmation,
    ImportAction.filter(
        F.action.in_({ImportActionValue.APPLY_MERGE, ImportActionValue.APPLY_REPLACE})
    ),
)
async def confirm_import(
    callback: CallbackQuery,
    callback_data: ImportAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    data = await state.get_data()
    document = data.get("import_document")
    if not isinstance(document, dict):
        await state.clear()
        await callback.answer(texts.SCREEN_EXPIRED, show_alert=True)
        return
    strategy = (
        "replace"
        if callback_data.action is ImportActionValue.APPLY_REPLACE
        else "merge"
    )
    include_strategy = _preview_has_existing_exercises(data.get("import_preview"))
    try:
        result = await api_client.import_data(
            callback.from_user.id, document, strategy
        )
    except InvalidRequestError:
        await state.clear()
        await callback.answer(texts.IMPORT_INVALID_FILE, show_alert=True)
        return
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    await state.clear()
    await callback.answer()
    await _render(
        callback,
        texts.import_completed(
            strategy=result.strategy,
            created=format_number(result.exercises_created),
            updated=format_number(result.existing_exercises_updated),
            entries=format_number(result.entries_imported),
            total_reps=format_number(result.total_reps_imported),
            include_strategy=include_strategy,
        ),
        settings_back_keyboard(),
    )


@router.callback_query(ImportAction.filter(F.action == ImportActionValue.CANCEL))
async def cancel_import(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer(texts.IMPORT_CANCELLED)
    await _render(callback, texts.IMPORT_CANCELLED, settings_back_keyboard())


@router.callback_query(
    SettingsAction.filter(F.action == SettingsActionValue.CHANGE_LANGUAGE)
)
async def choose_language(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await _render(callback, texts.CHOOSE_LANGUAGE, language_choices_keyboard())


@router.callback_query(
    SettingsAction.filter(F.action == SettingsActionValue.EXERCISE_MANAGEMENT)
)
async def show_exercise_management(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.answer()
    await _render(
        callback,
        texts.EXERCISE_MANAGEMENT,
        exercise_management_keyboard(),
    )


@router.callback_query(
    SettingsAction.filter(
        F.action.in_(
            {SettingsActionValue.CLEAR_HISTORY, SettingsActionValue.HARD_DELETE}
        )
    )
)
async def choose_managed_exercise(
    callback: CallbackQuery,
    callback_data: SettingsAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    await state.clear()
    try:
        exercises = await api_client.list_exercises(callback.from_user.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return
    is_clear = callback_data.action is SettingsActionValue.CLEAR_HISTORY
    text = (
        texts.CLEAR_HISTORY_CHOOSE_EXERCISE
        if is_clear
        else texts.DELETE_EXERCISE_CHOOSE_EXERCISE
    )
    operation = (
        ExerciseDetailActionValue.CLEAR_HISTORY
        if is_clear
        else ExerciseDetailActionValue.HARD_DELETE
    )
    await callback.answer()
    await _render(
        callback,
        text,
        exercise_management_selection_keyboard(exercises, operation=operation),
    )


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
            texts.language_changed(locale_name(settings.language)),
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
    if isinstance(callback.message, Message):
        chat = getattr(callback.message, "chat", None)
        message_id = getattr(callback.message, "message_id", None)
        chat_id = getattr(chat, "id", None)
        if isinstance(chat_id, int) and isinstance(message_id, int):
            await state.update_data(
                ui_chat_id=chat_id,
                ui_message_id=message_id,
            )
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
    state_data = await state.get_data()
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
        text = texts.settings(
            format_timezone(settings.timezone, language),
            locale_name(language),
        )
        markup = settings_keyboard()
        if isinstance(event, Message):
            chat_id = state_data.get("ui_chat_id")
            message_id = state_data.get("ui_message_id")
            await edit_stored_or_answer(
                event,
                text,
                markup,
                chat_id=chat_id if isinstance(chat_id, int) else None,
                message_id=message_id if isinstance(message_id, int) else None,
            )
        else:
            await _render(event, text, markup)
    finally:
        reset_current_language(token)


async def _render(
    event: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    *,
    parse_mode: ParseMode | None = None,
) -> None:
    if isinstance(event, CallbackQuery):
        if isinstance(event.message, Message):
            await edit_or_answer(
                event.message,
                text,
                reply_markup,
                parse_mode=parse_mode,
            )
        return
    await event.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


def _import_preview_text(preview: ImportPreview) -> str:
    return texts.import_preview(
        exercises=format_number(preview.exercises_count),
        entries=format_number(preview.entries_count),
        total_reps=format_number(preview.total_reps),
        date_from=(
            preview.date_from.strftime("%d.%m.%Y")
            if preview.date_from is not None
            else "—"
        ),
        date_to=(
            preview.date_to.strftime("%d.%m.%Y")
            if preview.date_to is not None
            else "—"
        ),
        new_count=format_number(len(preview.new_exercises)),
        existing_names=preview.existing_exercises,
    )


def _new_exercises_import_text(preview: ImportPreview) -> str:
    return texts.import_new_exercises_confirmation(
        exercises=format_number(preview.exercises_count),
        entries=format_number(preview.entries_count),
        total_reps=format_number(preview.total_reps),
        date_from=(
            preview.date_from.strftime("%d.%m.%Y")
            if preview.date_from is not None
            else "—"
        ),
        date_to=(
            preview.date_to.strftime("%d.%m.%Y")
            if preview.date_to is not None
            else "—"
        ),
        new_count=format_number(len(preview.new_exercises)),
    )


def _preview_has_existing_exercises(payload: object) -> bool:
    try:
        return bool(ImportPreview.model_validate(payload).existing_exercises)
    except (TypeError, ValueError):
        # Old/stale confirmations did not store preview data. Preserve their
        # previous result copy instead of guessing that the import was conflict-free.
        return True


async def _export_state(
    state: FSMContext,
) -> tuple[list[Exercise], set[int]] | None:
    data = await state.get_data()
    raw_exercises = data.get("export_exercises")
    raw_selected_ids = data.get("export_selected_ids")
    if not isinstance(raw_exercises, list) or not isinstance(raw_selected_ids, list):
        return None
    try:
        exercises = [Exercise.model_validate(value) for value in raw_exercises]
    except (TypeError, ValueError):
        return None
    if not all(isinstance(value, int) for value in raw_selected_ids):
        return None
    selected_ids = set(raw_selected_ids)
    if not selected_ids.issubset({exercise.id for exercise in exercises}):
        return None
    return exercises, selected_ids


def _export_entries_count(document: dict[str, object]) -> int:
    raw_exercises = document.get("exercises")
    if not isinstance(raw_exercises, list):
        return 0
    count = 0
    for exercise in raw_exercises:
        if not isinstance(exercise, dict):
            continue
        days = exercise.get("days")
        if not isinstance(days, list):
            continue
        for day in days:
            if isinstance(day, dict) and isinstance(day.get("entries"), list):
                count += len(day["entries"])
    return count


def _export_filename() -> str:
    created_at = datetime.now().astimezone()
    return created_at.strftime("repka-export-%Y-%m-%d_%H-%M-%S.json")
