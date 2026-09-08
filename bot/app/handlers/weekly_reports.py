import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.app.api.client import ApiError, RepTrackerApi, ResourceNotFoundError
from bot.app.handlers.common import answer_api_error
from bot.app.keyboards.exercises import ExerciseDetailAction, ExerciseDetailActionValue
from bot.app.texts import texts
from bot.app.services.telegram_delivery import send_with_rate_limit_retry

router = Router(name="weekly_reports")
logger = logging.getLogger(__name__)
_generating_cards: set[tuple[int, int, str | None]] = set()
_generating_reports: set[tuple[int, str]] = set()


async def _track_weekly_report_open(api_client, user_id: int) -> None:
    track_event = getattr(api_client, "track_event_safely", None)
    if track_event is not None:
        await track_event(user_id, "weekly_report_opened")


async def send_card(message, api_client, user_id, exercise_id, report_id=None):
    key = (user_id, exercise_id, report_id)
    if key in _generating_cards:
        return
    _generating_cards.add(key)
    try:
        png = await api_client.get_weekly_card(user_id, exercise_id, report_id)
        await send_with_rate_limit_retry(lambda: message.answer_photo(
            BufferedInputFile(png, filename=f"weekly-{exercise_id}.png")))
    except ResourceNotFoundError:
        await message.answer(texts.WEEKLY_NO_DATA)
    except Exception:
        logger.exception("Weekly card failed for exercise %s", exercise_id)
        await message.answer(texts.WEEKLY_CARD_FAILED)
    finally:
        _generating_cards.discard(key)


@router.callback_query(ExerciseDetailAction.filter(F.action == ExerciseDetailActionValue.WEEKLY_CARD))
async def exercise_weekly_card(callback: CallbackQuery, callback_data: ExerciseDetailAction,
                               api_client: RepTrackerApi):
    await callback.answer()
    await _track_weekly_report_open(api_client, callback.from_user.id)
    if isinstance(callback.message, Message):
        await send_card(callback.message, api_client, callback.from_user.id, callback_data.exercise_id)


@router.callback_query(F.data.startswith("weekly:"))
async def report_cards(callback: CallbackQuery, api_client: RepTrackerApi):
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    report_id = callback.data.split(":", 1)[1]
    key = (callback.from_user.id, report_id)
    if key in _generating_reports:
        return
    _generating_reports.add(key)
    try:
        try:
            report = await api_client.get_weekly_report(callback.from_user.id, report_id)
        except ApiError as error:
            await answer_api_error(callback.message, error)
            return
        await _track_weekly_report_open(api_client, callback.from_user.id)
        for exercise in report["exercises"]:
            await send_card(callback.message, api_client, callback.from_user.id,
                            exercise["exercise_id"], report_id)
    finally:
        _generating_reports.discard(key)
