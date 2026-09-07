from datetime import date
import re
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.app.api.client import Exercise, ImportPreview, ImportResult
from bot.app.handlers import settings
from bot.app.keyboards.settings import (
    ExportToggle,
    ImportAction,
    ImportActionValue,
)
from bot.app.states.settings import ExportData, ImportData
from bot.app.texts import reset_current_language, set_current_language


DOCUMENT = {
    "version": 1,
    "exercises": [
        {
            "name": "Pull-ups",
            "days": [{"date": "2026-08-01", "entries": [[10], [8, 7]]}],
        }
    ],
}


class FakeBot:
    async def download(self, file_id: str, destination) -> None:
        assert file_id == "file-1"
        destination.write(
            b'{"version":1,"exercises":[{"name":"Pull-ups","days":'
            b'[{"date":"2026-08-01","entries":[[10],[8,7]]}]}]}'
        )


class FakeMessage:
    def __init__(self, *, filename: str = "workouts.json") -> None:
        self.from_user = SimpleNamespace(id=42)
        self.chat = SimpleNamespace(id=2)
        self.message_id = 1
        self.document = SimpleNamespace(
            file_name=filename, file_size=200, file_id="file-1"
        )
        self.bot = FakeBot()
        self.answer = AsyncMock()
        self.answer_document = AsyncMock()
        self.edit_text = AsyncMock()


class FakeCallback:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=42)
        self.message = FakeMessage()
        self.answer = AsyncMock()


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )


@pytest.fixture(autouse=True)
def patch_event_types(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "Message", FakeMessage)
    monkeypatch.setattr(settings, "CallbackQuery", FakeCallback)
    token = set_current_language("en")
    yield
    reset_current_language(token)


def preview(*, conflicts: bool = True) -> ImportPreview:
    return ImportPreview(
        exercises_count=1,
        entries_count=2,
        total_reps=25,
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 1),
        new_exercises=[] if conflicts else ["Pull-ups"],
        existing_exercises=["Pull-ups"] if conflicts else [],
    )


def button_texts(markup: object) -> list[str]:
    return [
        button.text
        for row in markup.inline_keyboard  # type: ignore[attr-defined]
        for button in row
    ]


@pytest.mark.asyncio
async def test_json_file_is_previewed_without_importing(state: FSMContext) -> None:
    await state.set_state(ImportData.waiting_for_file)
    message = FakeMessage()
    api = SimpleNamespace(
        preview_import=AsyncMock(return_value=preview()),
        import_data=AsyncMock(),
    )

    await settings.receive_import_file(message, state, api)

    api.preview_import.assert_awaited_once_with(42, DOCUMENT)
    api.import_data.assert_not_awaited()
    assert await state.get_state() == ImportData.waiting_for_strategy.state
    rendered = message.answer.await_args.args[0]
    assert "Existing:\n• Pull-ups" in rendered
    assert "Workout entries: 2" in rendered


@pytest.mark.asyncio
async def test_import_screen_explains_format_and_renders_code_block() -> None:
    callback = FakeCallback()
    state = FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=2, user_id=3),
    )

    await settings.request_import_file(callback, state)

    args = callback.message.edit_text.await_args
    assert "exercises" in args.args[0]
    assert "&lt;pre&gt;" not in args.args[0]
    assert "<pre><code>" in args.args[0]
    assert args.kwargs["parse_mode"] == "HTML"
    assert await state.get_state() == ImportData.waiting_for_file.state


@pytest.mark.asyncio
async def test_export_selects_all_exercises_then_toggles_and_sends_json(
    state: FSMContext,
) -> None:
    callback = FakeCallback()
    exercises = [Exercise(id=7, name="Pull-ups"), Exercise(id=8, name="Plank")]
    api = SimpleNamespace(
        list_exercises=AsyncMock(return_value=exercises),
        export_data=AsyncMock(
            return_value={
                "version": 1,
                "exercises": [
                    {
                        "name": "Pull-ups",
                        "days": [
                            {"date": "2026-08-01", "entries": [[10], [8, 7]]}
                        ],
                    }
                ],
            }
        ),
    )

    await settings.request_export(callback, state, api)

    assert await state.get_state() == ExportData.selecting_exercises.state
    assert "Selected: 2 of 2" in callback.message.edit_text.await_args.args[0]
    assert button_texts(callback.message.edit_text.await_args.kwargs["reply_markup"]) == [
        "✅ Pull-ups",
        "✅ Plank",
        "📤 Export",
        "← Back",
    ]

    await settings.toggle_export_exercise(
        callback, ExportToggle(exercise_id=8), state
    )
    assert "Selected: 1 of 2" in callback.message.edit_text.await_args.args[0]

    await settings.export_selected_exercises(callback, state, api)

    api.export_data.assert_awaited_once_with(42, [7])
    assert callback.message.answer_document.await_count == 1
    document = callback.message.answer_document.await_args.args[0]
    assert re.fullmatch(
        r"repka-export-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.json",
        document.filename,
    )
    assert b'"version": 1' in document.data
    assert await state.get_state() is None
    assert "✅ Export ready" in callback.message.edit_text.await_args.args[0]


@pytest.mark.parametrize(
    ("language", "created_text", "import_button", "cancel_button", "forbidden"),
    [
        (
            "en",
            "New exercises to be created: 1",
            "Import",
            "Cancel",
            ("merge", "replace"),
        ),
        (
            "ru",
            "Будет создано новых упражнений: 1",
            "Импортировать",
            "Отмена",
            ("объедин", "замен"),
        ),
    ],
)
@pytest.mark.asyncio
async def test_no_conflicts_use_plain_import_confirmation_in_both_locales(
    state: FSMContext,
    language: str,
    created_text: str,
    import_button: str,
    cancel_button: str,
    forbidden: tuple[str, str],
) -> None:
    await state.set_state(ImportData.waiting_for_file)
    message = FakeMessage()
    api = SimpleNamespace(
        preview_import=AsyncMock(return_value=preview(conflicts=False))
    )

    token = set_current_language(language)
    try:
        await settings.receive_import_file(message, state, api)
    finally:
        reset_current_language(token)

    assert await state.get_state() == ImportData.waiting_for_confirmation.state
    rendered = message.answer.await_args.args[0]
    markup = message.answer.await_args.kwargs["reply_markup"]
    assert created_text in rendered
    assert button_texts(markup) == [import_button, cancel_button]
    visible_copy = f"{rendered}\n{' '.join(button_texts(markup))}".lower()
    assert all(term not in visible_copy for term in forbidden)


@pytest.mark.parametrize(
    ("language", "expected_buttons", "expected_prompt"),
    [
        (
            "en",
            ["🔀 Merge", "♻️ Replace", "❌ Cancel"],
            "How should existing history be handled?",
        ),
        (
            "ru",
            ["🔀 Объединить", "♻️ Заменить", "❌ Отмена"],
            "Как обработать существующую историю?",
        ),
    ],
)
@pytest.mark.asyncio
async def test_conflicts_keep_merge_replace_flow_in_both_locales(
    state: FSMContext,
    language: str,
    expected_buttons: list[str],
    expected_prompt: str,
) -> None:
    await state.set_state(ImportData.waiting_for_file)
    message = FakeMessage()
    api = SimpleNamespace(preview_import=AsyncMock(return_value=preview()))

    token = set_current_language(language)
    try:
        await settings.receive_import_file(message, state, api)
    finally:
        reset_current_language(token)

    assert await state.get_state() == ImportData.waiting_for_strategy.state
    assert expected_prompt in message.answer.await_args.args[0]
    assert button_texts(
        message.answer.await_args.kwargs["reply_markup"]
    ) == expected_buttons


@pytest.mark.asyncio
async def test_replace_requires_separate_final_confirmation(state: FSMContext) -> None:
    await state.set_state(ImportData.waiting_for_strategy)
    await state.update_data(
        import_document=DOCUMENT,
        import_preview=preview().model_dump(mode="json"),
    )
    callback = FakeCallback()

    await settings.choose_import_strategy(
        callback,
        ImportAction(action=ImportActionValue.REPLACE),
        state,
    )

    assert await state.get_state() == ImportData.waiting_for_confirmation.state
    assert "permanently deleted" in callback.message.edit_text.await_args.args[0]


@pytest.mark.asyncio
async def test_confirm_calls_import_once_and_clears_temporary_json(
    state: FSMContext,
) -> None:
    await state.set_state(ImportData.waiting_for_confirmation)
    await state.update_data(import_document=DOCUMENT)
    callback = FakeCallback()
    api = SimpleNamespace(
        import_data=AsyncMock(
            return_value=ImportResult(
                strategy="merge",
                exercises_created=1,
                existing_exercises_updated=0,
                entries_imported=2,
                total_reps_imported=25,
            )
        )
    )

    await settings.confirm_import(
        callback,
        ImportAction(action=ImportActionValue.APPLY_MERGE),
        state,
        api,
    )

    api.import_data.assert_awaited_once_with(42, DOCUMENT, "merge")
    assert await state.get_state() is None
    assert await state.get_data() == {}
    assert "✅ Import completed" in callback.message.edit_text.await_args.args[0]


@pytest.mark.parametrize(
    ("language", "completion", "forbidden"),
    [
        ("en", "✅ Import completed", ("merge", "replace")),
        ("ru", "✅ Импорт завершён", ("объедин", "замен")),
    ],
)
@pytest.mark.asyncio
async def test_no_conflict_result_omits_strategy_terminology(
    state: FSMContext,
    language: str,
    completion: str,
    forbidden: tuple[str, str],
) -> None:
    await state.set_state(ImportData.waiting_for_confirmation)
    await state.update_data(
        import_document=DOCUMENT,
        import_preview=preview(conflicts=False).model_dump(mode="json"),
    )
    callback = FakeCallback()
    api = SimpleNamespace(
        import_data=AsyncMock(
            return_value=ImportResult(
                strategy="merge",
                exercises_created=1,
                existing_exercises_updated=0,
                entries_imported=2,
                total_reps_imported=25,
            )
        )
    )

    token = set_current_language(language)
    try:
        await settings.confirm_import(
            callback,
            ImportAction(action=ImportActionValue.APPLY_MERGE),
            state,
            api,
        )
    finally:
        reset_current_language(token)

    rendered = callback.message.edit_text.await_args.args[0]
    assert completion in rendered
    assert all(term not in rendered.lower() for term in forbidden)


@pytest.mark.asyncio
async def test_cancel_clears_json_and_never_calls_backend(state: FSMContext) -> None:
    await state.set_state(ImportData.waiting_for_confirmation)
    await state.update_data(import_document=DOCUMENT)
    callback = FakeCallback()

    await settings.cancel_import(callback, state)

    assert await state.get_state() is None
    assert await state.get_data() == {}
    assert callback.message.edit_text.await_args.args[0] == "Import cancelled"


@pytest.mark.asyncio
async def test_non_json_file_is_rejected_before_preview(state: FSMContext) -> None:
    message = FakeMessage(filename="workouts.csv")
    api = SimpleNamespace(preview_import=AsyncMock())

    await settings.receive_import_file(message, state, api)

    api.preview_import.assert_not_awaited()
    assert message.answer.await_args.args[0] == "Only .json files are supported."
