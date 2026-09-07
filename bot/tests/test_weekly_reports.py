from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from aiogram.methods import SendMessage
from aiogram.types import Message

from bot.app.api.client import RepTrackerApi, UnexpectedApiError, ResourceNotFoundError
from bot.app.handlers.weekly_reports import exercise_weekly_card, report_cards
from bot.app.keyboards.exercises import (
    ExerciseDetailAction,
    ExerciseDetailActionValue,
    exercise_statistics_keyboard,
)
from bot.app.services.weekly_report import report_keyboard, split_summary, summary_text
from bot.app.texts import reset_current_language, set_current_language
from bot.app.workers.weekly_reports import deliver_leased_reports, materialize_all


def report(language="ru"):
    item = dict(exercise_id=1, name="Pull-ups", total=354, previous=396, delta=-42,
                percent=-42 / 396 * 100, active_days=5, best_day=dict(date="2026-08-29", reps=85))
    return dict(id="a-report", external_id="123", lock_token="lease-token", language=language,
                week_start="2026-08-24", week_end="2026-08-30",
                exercises=[item, {**item, "exercise_id": 2, "name": "Squats"}])


@pytest.mark.parametrize("language", ["ru", "en"])
def test_summary_and_buttons(language):
    data = report(language)
    text = summary_text(data)
    assert "Pull-ups" in text and "Squats" in text
    assert "24.08 — 30.08" in text
    assert ("🔴 ▼ 42 (−10,6%)" if language == "ru" else "🔴 ▼ 42 (−10.6%)") in text
    assert "29.08 — 85" not in text
    assert report_keyboard(data).inline_keyboard[0][0].text == (
        "🖼 Сгенерировать карточки" if language == "ru" else "🖼 Generate cards")
    assert report_keyboard(data).inline_keyboard[0][0].style == "primary"
    token = set_current_language(language)
    try:
        buttons = [
            button
            for row in exercise_statistics_keyboard(9, weekly_report_enabled=True).inline_keyboard
            for button in row
        ]
        card = next(b for b in buttons if "weekly_card" in b.callback_data)
        assert card.text == ("🖼 Картинка недели" if language == "ru" else "🖼 Weekly card")
        assert ExerciseDetailAction.unpack(card.callback_data).exercise_id == 9
    finally:
        reset_current_language(token)


def test_first_week_and_summary_is_split_at_telegram_limit():
    data = report()
    item = data["exercises"][0]
    item.update(previous=None, delta=None, percent=None)
    assert "Предыдущей полной недели ещё нет." in summary_text(data)
    data["exercises"] = [{**item, "exercise_id": index, "name": f"Exercise {index}"}
                         for index in range(200)]
    messages = split_summary(data)
    assert len(messages) > 1
    assert all(len(message) <= 4096 for message in messages)


@pytest.mark.asyncio
async def test_worker_materializes_pages_and_delivers_leased_report(monkeypatch):
    api = SimpleNamespace(
        materialize_weekly_reports=AsyncMock(side_effect=[
            dict(next_cursor=7), dict(next_cursor=None),
        ]),
        lease_weekly_reports=AsyncMock(return_value=dict(reports=[report()])),
        complete_weekly_delivery=AsyncMock(),
    )
    bot = SimpleNamespace(send_message=AsyncMock())
    pause = AsyncMock()
    from bot.app.workers import weekly_reports
    monkeypatch.setattr(weekly_reports.asyncio, "sleep", pause)

    await materialize_all(api)
    assert api.materialize_weekly_reports.await_args_list[1].args == (7,)
    assert await deliver_leased_reports(bot, api, "worker-a") == 1
    bot.send_message.assert_awaited_once()
    api.complete_weekly_delivery.assert_awaited_once_with("a-report", "lease-token", "sent")
    pause.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_worker_returns_telegram_rate_limit_to_queue(monkeypatch):
    from aiogram.exceptions import TelegramRetryAfter
    api = SimpleNamespace(
        lease_weekly_reports=AsyncMock(return_value=dict(reports=[report()])),
        complete_weekly_delivery=AsyncMock(),
    )
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=TelegramRetryAfter(
        method=SendMessage(chat_id=123, text="report"), message="slow down", retry_after=7,
    )))
    from bot.app.workers import weekly_reports
    monkeypatch.setattr(weekly_reports.asyncio, "sleep", AsyncMock())

    await deliver_leased_reports(bot, api, "worker-a")
    call = api.complete_weekly_delivery.await_args
    assert call.args == ("a-report", "lease-token", "retry")
    assert call.kwargs["retry_after_seconds"] == 7
    assert call.kwargs["error"].startswith("TelegramRetryAfter:")


def callback(data="weekly:a-report"):
    message = Mock(spec=Message)
    message.answer_photo = AsyncMock()
    message.answer = AsyncMock()
    return SimpleNamespace(data=data, from_user=SimpleNamespace(id=123), message=message, answer=AsyncMock())


@pytest.mark.asyncio
async def test_generate_cards_continues_after_failure():
    cb = callback()
    api = SimpleNamespace(get_weekly_report=AsyncMock(return_value=report()),
                          get_weekly_card=AsyncMock(side_effect=[RuntimeError("render"), b"png"]))
    await report_cards(cb, api)
    cb.answer.assert_awaited_once()
    assert api.get_weekly_card.await_count == 2
    assert api.get_weekly_card.call_args_list[1].args == (123, 2, "a-report")
    cb.message.answer.assert_awaited_once()
    cb.message.answer_photo.assert_awaited_once()


@pytest.mark.asyncio
async def test_exercise_card_and_no_data():
    cb = callback()
    api = SimpleNamespace(get_weekly_card=AsyncMock(return_value=b"png"))
    data = ExerciseDetailAction(action=ExerciseDetailActionValue.WEEKLY_CARD, exercise_id=8)
    await exercise_weekly_card(cb, data, api)
    api.get_weekly_card.assert_awaited_once_with(123, 8, None)
    cb.message.answer_photo.assert_awaited_once()
    api.get_weekly_card.side_effect = ResourceNotFoundError()
    await exercise_weekly_card(cb, data, api)
    cb.message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_png_client_identity_period_and_validation():
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, content=b"\x89PNG\r\n\x1a\nexample")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle), base_url="http://api") as http:
        api = RepTrackerApi("http://api", client=http)
        await api.get_weekly_card(123, 8, "saved")
    assert dict(requests[0].url.params) == {"provider": "telegram", "external_id": "123", "report_id": "saved"}
    assert requests[0].extensions["timeout"]["read"] == 60
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, text="bad")), base_url="http://api") as http:
        with pytest.raises(UnexpectedApiError):
            await RepTrackerApi("http://api", client=http).get_weekly_card(123, 8)
