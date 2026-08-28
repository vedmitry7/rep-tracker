from dataclasses import dataclass, replace
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.app.api.client import ApiError, Exercise, RepTrackerApi
from bot.app.handlers.common import answer_api_error
from bot.app.handlers.exercises import show_exercise
from bot.app.keyboards.exercises import exercise_screen_keyboard
from bot.app.keyboards.results import (
    ConstructorAction,
    ConstructorActionValue,
    DateChoice,
    DateChoiceValue,
    OpenDatePicker,
    RepetitionAction,
    RepetitionActionValue,
    ResultAction,
    ResultActionValue,
    ResultScreen,
    constructor_keyboard,
    date_picker_keyboard,
    manual_date_keyboard,
    result_input_keyboard,
)
from bot.app.services.date_parser import (
    DateParseError,
    days_ago,
    format_result_date,
    parse_result_date,
)
from bot.app.services.result_constructor import (
    ConstructorError,
    add_set,
    change_repetition,
    initial_repetitions,
    remove_set,
)
from bot.app.services.result_parser import ResultParseError, parse_result
from bot.app.states.result import AddResult
from bot.app.texts import texts


router = Router(name=__name__)

RESULT_STATES = {
    AddResult.entering_result.state,
    AddResult.choosing_date.state,
    AddResult.entering_date.state,
    AddResult.constructor.state,
}


@dataclass(frozen=True)
class ResultContext:
    exercise_id: int
    exercise_name: str
    user_today: date
    performed_on: date
    reps: list[int]

    @classmethod
    def from_data(cls, data: dict[str, object]) -> "ResultContext | None":
        exercise_id = data.get("exercise_id")
        exercise_name = data.get("exercise_name")
        user_today = data.get("user_today")
        performed_on = data.get("performed_on")
        repetitions = data.get("reps")
        if (
            not isinstance(exercise_id, int)
            or not isinstance(exercise_name, str)
            or type(user_today) is not date
            or type(performed_on) is not date
            or not isinstance(repetitions, list)
            or not all(isinstance(item, int) for item in repetitions)
        ):
            return None
        return cls(
            exercise_id=exercise_id,
            exercise_name=exercise_name,
            user_today=user_today,
            performed_on=performed_on,
            reps=list(repetitions),
        )

    def as_fsm_data(self) -> dict[str, object]:
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "user_today": self.user_today,
            "performed_on": self.performed_on,
            "reps": list(self.reps),
        }


@router.callback_query(
    ResultAction.filter(F.action == ResultActionValue.START),
)
async def start_result_flow(
    callback: CallbackQuery,
    callback_data: ResultAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    try:
        exercises = await api_client.list_exercises(callback.from_user.id)
        settings = await api_client.get_user_settings(callback.from_user.id)
    except ApiError as error:
        await answer_api_error(callback, error)
        return

    exercise = next(
        (item for item in exercises if item.id == callback_data.exercise_id),
        None,
    )
    if exercise is None:
        await callback.answer(texts.EXERCISE_NOT_FOUND, show_alert=True)
        return

    context = ResultContext(
        exercise_id=exercise.id,
        exercise_name=exercise.name,
        user_today=settings.today,
        performed_on=settings.today,
        reps=[],
    )
    await state.set_state(AddResult.entering_result)
    await state.set_data(context.as_fsm_data())
    await callback.answer()
    await _render_result_input(callback, context)


@router.message(AddResult.entering_result)
async def save_text_result(
    message: Message,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    try:
        repetitions = parse_result(message.text or "")
    except ResultParseError as error:
        await message.answer(str(error))
        return

    if message.from_user is None:
        return
    context = await _get_context(message, state)
    if context is None:
        return
    context = replace(context, reps=repetitions)
    await state.update_data(reps=list(repetitions))
    await _save_result(message, state, api_client, message.from_user.id, context)


@router.callback_query(
    ResultAction.filter(F.action == ResultActionValue.OPEN_CONSTRUCTOR),
)
async def open_constructor(
    callback: CallbackQuery,
    callback_data: ResultAction,
    state: FSMContext,
) -> None:
    if await state.get_state() != AddResult.entering_result.state:
        await callback.answer(texts.SCREEN_EXPIRED)
        return
    context = await _get_context(callback, state)
    if context is None:
        return
    if context.exercise_id != callback_data.exercise_id:
        await callback.answer(texts.SCREEN_EXPIRED)
        return

    context = replace(context, reps=initial_repetitions(context.reps))
    await state.update_data(reps=list(context.reps))
    await state.set_state(AddResult.constructor)
    await callback.answer()
    await _render_constructor(callback, context)


@router.callback_query(OpenDatePicker.filter())
async def open_date_picker(
    callback: CallbackQuery,
    callback_data: OpenDatePicker,
    state: FSMContext,
) -> None:
    expected_state = (
        AddResult.entering_result.state
        if callback_data.return_to == ResultScreen.INPUT
        else AddResult.constructor.state
    )
    if await state.get_state() != expected_state:
        await callback.answer(texts.SCREEN_EXPIRED)
        return
    context = await _get_context(callback, state)
    if context is None:
        return
    await state.update_data(return_screen=callback_data.return_to.value)
    await state.set_state(AddResult.choosing_date)
    await callback.answer()
    await _render(
        callback,
        texts.CHOOSE_DATE,
        date_picker_keyboard(context.exercise_id),
    )


@router.callback_query(DateChoice.filter())
async def choose_date(
    callback: CallbackQuery,
    callback_data: DateChoice,
    state: FSMContext,
) -> None:
    if await state.get_state() not in {
        AddResult.choosing_date.state,
        AddResult.entering_date.state,
    }:
        await callback.answer(texts.SCREEN_EXPIRED)
        return
    context = await _get_context(callback, state)
    if context is None:
        return

    if callback_data.choice == DateChoiceValue.MANUAL:
        await state.set_state(AddResult.entering_date)
        await callback.answer()
        await _render(
            callback,
            texts.ENTER_DATE,
            manual_date_keyboard(context.exercise_id),
        )
        return

    if callback_data.choice == DateChoiceValue.BACK:
        await callback.answer()
        await _return_to_previous_screen(callback, state, context)
        return

    offsets = {
        DateChoiceValue.TODAY: 0,
        DateChoiceValue.YESTERDAY: 1,
        DateChoiceValue.DAY_BEFORE_YESTERDAY: 2,
    }
    selected_date = days_ago(
        offsets[callback_data.choice],
        today=context.user_today,
    )
    context = replace(context, performed_on=selected_date)
    await state.update_data(performed_on=selected_date)
    await callback.answer()
    await _return_to_previous_screen(callback, state, context)


@router.message(AddResult.entering_date)
async def enter_date(message: Message, state: FSMContext) -> None:
    try:
        context = await _get_context(message, state)
        if context is None:
            return
        selected_date = parse_result_date(
            message.text or "",
            today=context.user_today,
        )
    except DateParseError as error:
        await message.answer(str(error))
        return

    context = replace(context, performed_on=selected_date)
    await state.update_data(performed_on=selected_date)
    await _return_to_previous_screen(message, state, context)


@router.callback_query(RepetitionAction.filter())
async def change_constructor_repetition(
    callback: CallbackQuery,
    callback_data: RepetitionAction,
    state: FSMContext,
) -> None:
    if not await _ensure_constructor_state(callback, state):
        return
    context = await _get_context(callback, state)
    if context is None:
        return

    if callback_data.action == RepetitionActionValue.VALUE:
        await callback.answer()
        return

    delta = (
        1
        if callback_data.action == RepetitionActionValue.INCREMENT
        else -1
    )
    try:
        repetitions = change_repetition(
            context.reps,
            callback_data.index,
            delta,
        )
    except ConstructorError as error:
        await callback.answer(str(error), show_alert=True)
        return

    if repetitions == context.reps:
        boundary = texts.MIN_REPETITIONS if delta < 0 else texts.MAX_REPETITIONS
        await callback.answer(boundary)
        return

    context = replace(context, reps=repetitions)
    await state.update_data(reps=list(repetitions))
    await callback.answer()
    await _render_constructor(callback, context)


@router.callback_query(ConstructorAction.filter())
async def constructor_action(
    callback: CallbackQuery,
    callback_data: ConstructorAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    if not await _ensure_constructor_state(callback, state):
        return
    context = await _get_context(callback, state)
    if context is None:
        return

    if callback_data.action == ConstructorActionValue.SAVE:
        await _save_result(
            callback,
            state,
            api_client,
            callback.from_user.id,
            context,
        )
        return
    if callback_data.action == ConstructorActionValue.BACK:
        await state.set_state(AddResult.entering_result)
        await callback.answer()
        await _render_result_input(callback, context)
        return

    try:
        if callback_data.action == ConstructorActionValue.ADD_SET:
            repetitions = add_set(context.reps)
        else:
            repetitions = remove_set(context.reps)
    except ConstructorError as error:
        await callback.answer(str(error))
        return

    context = replace(context, reps=repetitions)
    await state.update_data(reps=list(repetitions))
    await callback.answer()
    await _render_constructor(callback, context)


@router.callback_query(
    ResultAction.filter(F.action == ResultActionValue.CANCEL),
)
async def cancel_result_flow(
    callback: CallbackQuery,
    callback_data: ResultAction,
    state: FSMContext,
    api_client: RepTrackerApi,
) -> None:
    current_state = await state.get_state()
    context = ResultContext.from_data(await state.get_data())
    if (
        current_state not in RESULT_STATES
        or context is None
        or context.exercise_id != callback_data.exercise_id
    ):
        await callback.answer(texts.INPUT_FINISHED)
        return

    await state.clear()
    await callback.answer(texts.INPUT_CANCELLED)
    if isinstance(callback.message, Message):
        try:
            stats = await api_client.get_exercise_stats(
                callback.from_user.id,
                context.exercise_id,
            )
        except ApiError as error:
            await answer_api_error(callback, error)
            return
        await show_exercise(
            callback.message,
            Exercise(id=context.exercise_id, name=context.exercise_name),
            stats,
        )


async def _save_result(
    event: Message | CallbackQuery,
    state: FSMContext,
    api_client: RepTrackerApi,
    telegram_user_id: int,
    context: ResultContext,
) -> bool:
    try:
        entry = await api_client.create_exercise_entry(
            telegram_user_id,
            context.exercise_id,
            context.reps,
            performed_on=context.performed_on,
        )
    except ApiError as error:
        await answer_api_error(event, error)
        return False

    await state.clear()
    formatted_reps = " • ".join(str(value) for value in entry.reps)
    text = texts.result_saved(
        context.exercise_name,
        formatted_reps,
        sum(entry.reps),
        entry.performed_on.strftime("%d.%m.%Y"),
    )
    if isinstance(event, CallbackQuery):
        await event.answer(texts.RESULT_ADDED)
    await _render(
        event,
        text,
        exercise_screen_keyboard(context.exercise_id),
    )
    return True


async def _get_context(
    event: Message | CallbackQuery,
    state: FSMContext,
) -> ResultContext | None:
    context = ResultContext.from_data(await state.get_data())
    if context is not None:
        return context
    await state.clear()
    text = texts.RESTORE_INPUT_FAILED
    if isinstance(event, CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text)
    return None


async def _ensure_constructor_state(
    callback: CallbackQuery,
    state: FSMContext,
) -> bool:
    if await state.get_state() == AddResult.constructor.state:
        return True
    await callback.answer(texts.SCREEN_EXPIRED)
    return False


async def _return_to_previous_screen(
    event: Message | CallbackQuery,
    state: FSMContext,
    context: ResultContext,
) -> None:
    data = await state.get_data()
    try:
        return_screen = ResultScreen(data.get("return_screen", ResultScreen.INPUT))
    except ValueError:
        return_screen = ResultScreen.INPUT

    if return_screen == ResultScreen.CONSTRUCTOR:
        await state.set_state(AddResult.constructor)
        await _render_constructor(event, context)
    else:
        await state.set_state(AddResult.entering_result)
        await _render_result_input(event, context)


async def _render_result_input(
    event: Message | CallbackQuery,
    context: ResultContext,
) -> None:
    text = texts.result_input(
        context.exercise_name,
        format_result_date(context.performed_on, today=context.user_today),
    )
    await _render(event, text, result_input_keyboard(context.exercise_id))


async def _render_constructor(
    event: Message | CallbackQuery,
    context: ResultContext,
) -> None:
    sets = "\n".join(
        f"{index}. {value}" for index, value in enumerate(context.reps, start=1)
    )
    text = texts.result_constructor(
        context.exercise_name,
        format_result_date(context.performed_on, today=context.user_today),
        sets,
    )
    await _render(
        event,
        text,
        constructor_keyboard(context.exercise_id, context.reps),
    )


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
