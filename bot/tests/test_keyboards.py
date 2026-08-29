from bot.app.api.client import Exercise
from bot.app.keyboards.exercises import (
    ExerciseAction,
    ExerciseActionValue,
    ExerciseDetailAction,
    ExerciseDetailActionValue,
    ExerciseOpen,
    ExercisePreset,
    exercise_back_keyboard,
    exercise_destructive_confirmation_keyboard,
    exercise_presets_keyboard,
    exercise_screen_keyboard,
    exercises_list_keyboard,
)
from bot.app.keyboards.results import (
    ResultAction,
    ResultActionValue,
)
from bot.app.keyboards.settings import SettingsAction, SettingsActionValue


def callback_values(markup: object) -> list[str]:
    return [
        button.callback_data
        for row in markup.inline_keyboard  # type: ignore[attr-defined]
        for button in row
        if button.callback_data is not None
    ]


def test_preset_keyboard_uses_typed_callback_data() -> None:
    callbacks = callback_values(exercise_presets_keyboard())

    presets = [ExercisePreset.unpack(value).name for value in callbacks[:4]]
    custom = ExerciseAction.unpack(callbacks[4])
    back = ExerciseAction.unpack(callbacks[5])

    assert presets == ["Подтягивания", "Отжимания", "Приседания", "Брусья"]
    assert custom.action == ExerciseActionValue.CUSTOM
    assert back.action == ExerciseActionValue.LIST


def test_preset_keyboard_hides_existing_normalized_names() -> None:
    markup = exercise_presets_keyboard(
        [
            Exercise(id=1, name=" подтягивания "),
            Exercise(id=2, name="ОТЖИМАНИЯ"),
            Exercise(id=3, name="Приседания"),
        ]
    )
    callbacks = callback_values(markup)

    presets = [
        ExercisePreset.unpack(value).name
        for value in callbacks
        if value.startswith("exercise_preset:")
    ]
    assert presets == ["Брусья"]


def test_exercise_list_contains_open_and_add_callbacks() -> None:
    markup = exercises_list_keyboard(
        [
            Exercise(id=10, name="Подтягивания"),
            Exercise(id=11, name="Отжимания"),
        ]
    )
    callbacks = callback_values(markup)

    assert [ExerciseOpen.unpack(value).exercise_id for value in callbacks[:2]] == [
        10,
        11,
    ]
    assert ExerciseAction.unpack(callbacks[2]).action == ExerciseActionValue.ADD
    assert SettingsAction.unpack(callbacks[3]).action == SettingsActionValue.OPEN


def test_exercise_screen_result_callback_keeps_exercise_id() -> None:
    markup = exercise_screen_keyboard(exercise_id=42)
    callbacks = callback_values(markup)

    result_action = ResultAction.unpack(callbacks[0])
    detail_actions = [ExerciseDetailAction.unpack(value) for value in callbacks[1:3]]
    list_action = ExerciseAction.unpack(callbacks[3])

    assert result_action.action == ResultActionValue.START
    assert result_action.exercise_id == 42
    assert [(item.action, item.exercise_id) for item in detail_actions] == [
        (ExerciseDetailActionValue.STATISTICS, 42),
        (ExerciseDetailActionValue.HISTORY, 42),
    ]
    assert list_action.action == ExerciseActionValue.LIST
    assert [len(row) for row in markup.inline_keyboard] == [1, 1, 1, 1]
    assert [button.text for row in markup.inline_keyboard for button in row] == [
        "➕ Добавить результат",
        "📊 Статистика",
        "📜 История",
        "◀️ Упражнения",
    ]
    assert markup.inline_keyboard[0][0].style == "primary"


def test_back_button_returns_to_correct_exercise() -> None:
    callbacks = callback_values(exercise_back_keyboard(exercise_id=42))

    assert len(callbacks) == 1
    assert ExerciseOpen.unpack(callbacks[0]).exercise_id == 42


def test_destructive_cancel_returns_without_mutating() -> None:
    markup = exercise_destructive_confirmation_keyboard(
        42, operation="clear_history"
    )
    callbacks = callback_values(markup)

    confirm = ExerciseDetailAction.unpack(callbacks[0])
    cancel = SettingsAction.unpack(callbacks[1])
    assert confirm.action == ExerciseDetailActionValue.CONFIRM_CLEAR_HISTORY
    assert confirm.exercise_id == 42
    assert cancel.action == SettingsActionValue.CLEAR_HISTORY
    assert markup.inline_keyboard[0][0].style == "danger"
