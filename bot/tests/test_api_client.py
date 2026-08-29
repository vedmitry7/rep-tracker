from collections.abc import Callable
from datetime import date
import json

import httpx
import pytest

from bot.app.api.client import (
    AccessForbiddenError,
    BackendUnavailableError,
    RepTrackerApi,
    ResourceConflictError,
    ResourceNotFoundError,
    UnexpectedApiError,
)


def build_api(
    handler: Callable[[httpx.Request], httpx.Response],
) -> RepTrackerApi:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://backend.test",
    )
    return RepTrackerApi("http://unused.test", client=client)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "created"),
    [(200, False), (201, True)],
)
async def test_resolve_user_maps_status_to_created(
    status_code: int,
    created: bool,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/users/resolve"
        assert request.read() == (
            b'{"provider":"telegram","external_id":"12345",'
            b'"default_timezone":"Europe/Madrid","default_language":"ru"}'
        )
        return httpx.Response(status_code, json={"id": 1, "language": "ru"})

    api = build_api(handler)

    result = await api.resolve_user(12345, "Europe/Madrid", "ru")

    assert result.created is created
    assert result.language == "ru"


@pytest.mark.asyncio
async def test_list_exercises_sends_identity_as_query_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/exercises"
        assert dict(request.url.params) == {
            "provider": "telegram",
            "external_id": "777",
        }
        return httpx.Response(
            200,
            json=[{"id": 4, "name": "Подтягивания", "ignored": True}],
        )

    api = build_api(handler)

    exercises = await api.list_exercises(777)

    assert [(item.id, item.name) for item in exercises] == [(4, "Подтягивания")]


@pytest.mark.asyncio
async def test_get_and_update_user_settings() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            assert request.url.path == "/users/settings"
            assert dict(request.url.params) == {
                "provider": "telegram",
                "external_id": "777",
            }
            return httpx.Response(
                200,
                json={
                    "timezone": "Europe/Moscow",
                    "today": "2026-08-27",
                    "language": "ru",
                },
            )
        assert request.method == "PATCH"
        assert json.loads(request.content) == {
            "provider": "telegram",
            "external_id": "777",
            "timezone": "Europe/Madrid",
        }
        return httpx.Response(
            200,
            json={
                "timezone": "Europe/Madrid",
                "today": "2026-08-27",
                "language": "ru",
            },
        )

    api = build_api(handler)
    current = await api.get_user_settings(777)
    updated = await api.update_user_timezone(777, "Europe/Madrid")

    assert len(requests) == 2
    assert current.timezone == "Europe/Moscow"
    assert updated.timezone == "Europe/Madrid"
    assert current.language == "ru"


@pytest.mark.asyncio
async def test_update_user_language_uses_settings_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/users/settings"
        assert json.loads(request.content) == {
            "provider": "telegram",
            "external_id": "777",
            "language": "en",
        }
        return httpx.Response(
            200,
            json={
                "timezone": "Europe/Moscow",
                "today": "2026-08-27",
                "language": "en",
            },
        )

    updated = await build_api(handler).update_user_language(777, "en")

    assert updated.language == "en"


@pytest.mark.asyncio
async def test_create_exercise_sends_identity_and_name() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/exercises"
        assert request.read() == (
            b'{"provider":"telegram","external_id":"777",'
            b'"name":"\xd0\x91\xd1\x80\xd1\x83\xd1\x81\xd1\x8c\xd1\x8f"}'
        )
        return httpx.Response(201, json={"id": 9, "name": "Брусья"})

    api = build_api(handler)

    exercise = await api.create_exercise(777, "Брусья")

    assert exercise.id == 9
    assert exercise.name == "Брусья"


@pytest.mark.asyncio
async def test_create_exercise_entry_sends_result_and_date() -> None:
    performed_on = date(2026, 8, 27)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/exercise-entries"
        assert json.loads(request.content) == {
            "provider": "telegram",
            "external_id": "777",
            "exercise_id": 9,
            "reps": [10, 9, 8, 7],
            "performed_on": "2026-08-27",
        }
        return httpx.Response(
            201,
            json={
                "id": 15,
                "exercise_id": 9,
                "reps": [10, 9, 8, 7],
                "performed_on": "2026-08-27",
            },
        )

    api = build_api(handler)

    entry = await api.create_exercise_entry(
        777,
        exercise_id=9,
        reps=[10, 9, 8, 7],
        performed_on=performed_on,
    )

    assert entry.id == 15
    assert entry.exercise_id == 9
    assert entry.reps == [10, 9, 8, 7]
    assert entry.performed_on == performed_on


@pytest.mark.asyncio
async def test_get_exercise_stats_sends_identity() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/exercises/9/stats"
        assert dict(request.url.params) == {
            "provider": "telegram",
            "external_id": "777",
        }
        return httpx.Response(
            200,
            json={
                "total_reps": 1284,
                "today": "2026-08-27",
                "today_reps": 34,
                "last_7_days_reps": 126,
                "last_30_days_reps": 483,
                "all_time_entries": 35,
                "active_days": 22,
                "best_day": {"date": "2026-08-20", "reps": 85},
                "last_entry": {
                    "id": 15,
                    "exercise_id": 9,
                    "reps": [10, 9, 8, 7],
                    "performed_on": "2026-08-27",
                    "created_at": "2026-08-27T10:00:00Z",
                },
            },
        )

    stats = await build_api(handler).get_exercise_stats(777, 9)

    assert stats.total_reps == 1284
    assert stats.best_day is not None
    assert stats.best_day.reps == 85
    assert stats.last_entry is not None
    assert stats.last_entry.reps == [10, 9, 8, 7]


@pytest.mark.asyncio
async def test_get_exercise_entries_requests_latest_ten() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/exercises/9/entries"
        assert dict(request.url.params) == {
            "provider": "telegram",
            "external_id": "777",
            "limit": "10",
            "offset": "0",
        }
        return httpx.Response(
            200,
            json=[
                {
                    "id": 15,
                    "exercise_id": 9,
                    "reps": [10],
                    "performed_on": "2026-08-27",
                    "created_at": "2026-08-27T10:00:00Z",
                }
            ],
        )

    entries = await build_api(handler).get_exercise_entries(777, 9)

    assert len(entries) == 1
    assert entries[0].id == 15


@pytest.mark.asyncio
async def test_get_exercise_entries_supports_day_filter() -> None:
    selected_date = date(2026, 8, 27)

    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {
            "provider": "telegram",
            "external_id": "777",
            "limit": "100",
            "offset": "0",
            "from": "2026-08-27",
            "to": "2026-08-27",
        }
        return httpx.Response(200, json=[])

    entries = await build_api(handler).get_exercise_entries(
        777,
        9,
        limit=100,
        from_date=selected_date,
        to_date=selected_date,
    )

    assert entries == []


@pytest.mark.asyncio
async def test_get_exercise_history_days() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/exercises/9/history-days"
        assert dict(request.url.params) == {
            "provider": "telegram",
            "external_id": "777",
            "limit": "10",
            "offset": "0",
        }
        return httpx.Response(
            200,
            json=[
                {
                    "date": "2026-08-27",
                    "total_reps": 74,
                    "entries_count": 2,
                }
            ],
        )

    days = await build_api(handler).get_exercise_history_days(777, 9)

    assert len(days) == 1
    assert days[0].date == date(2026, 8, 27)
    assert days[0].total_reps == 74


@pytest.mark.asyncio
async def test_update_exercise_entry_uses_patch_and_keeps_entry_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/exercise-entries/15"
        assert json.loads(request.content) == {
            "provider": "telegram",
            "external_id": "777",
            "reps": [11, 10, 9],
        }
        return httpx.Response(
            200,
            json={
                "id": 15,
                "exercise_id": 9,
                "reps": [11, 10, 9],
                "performed_on": "2026-08-27",
                "created_at": "2026-08-27T10:00:00Z",
            },
        )

    entry = await build_api(handler).update_exercise_entry(
        777,
        15,
        reps=[11, 10, 9],
    )

    assert entry.id == 15
    assert entry.reps == [11, 10, 9]


@pytest.mark.asyncio
async def test_update_exercise_entry_date() -> None:
    selected_date = date(2026, 8, 25)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert json.loads(request.content)["performed_on"] == "2026-08-25"
        return httpx.Response(
            200,
            json={
                "id": 15,
                "exercise_id": 9,
                "reps": [10],
                "performed_on": "2026-08-25",
            },
        )

    entry = await build_api(handler).update_exercise_entry(
        777,
        15,
        performed_on=selected_date,
    )

    assert entry.performed_on == selected_date


@pytest.mark.asyncio
async def test_delete_exercise_entry() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/exercise-entries/15"
        assert dict(request.url.params) == {
            "provider": "telegram",
            "external_id": "777",
        }
        return httpx.Response(204)

    await build_api(handler).delete_exercise_entry(777, 15)


@pytest.mark.asyncio
async def test_preview_and_apply_import_send_identity_document_and_strategy() -> None:
    document = {
        "version": 1,
        "exercises": [
            {
                "name": "Pull-ups",
                "days": [{"date": "2026-08-01", "entries": [[10]]}],
            }
        ],
    }
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = json.loads(request.content)
        assert payload["provider"] == "telegram"
        assert payload["external_id"] == "777"
        assert payload["document"] == document
        if request.url.path.endswith("/preview"):
            return httpx.Response(
                200,
                json={
                    "exercises_count": 1,
                    "entries_count": 1,
                    "total_reps": 10,
                    "date_from": "2026-08-01",
                    "date_to": "2026-08-01",
                    "new_exercises": ["Pull-ups"],
                    "existing_exercises": [],
                },
            )
        assert payload["strategy"] == "replace"
        return httpx.Response(
            201,
            json={
                "strategy": "replace",
                "exercises_created": 1,
                "existing_exercises_updated": 0,
                "entries_imported": 1,
                "total_reps_imported": 10,
            },
        )

    api = build_api(handler)
    preview = await api.preview_import(777, document)
    result = await api.import_data(777, document, "replace")

    assert [request.url.path for request in requests] == [
        "/imports/preview",
        "/imports",
    ]
    assert preview.entries_count == 1
    assert result.strategy == "replace"


@pytest.mark.asyncio
async def test_clear_and_permanent_delete_use_distinct_api_paths() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert dict(request.url.params) == {
            "provider": "telegram",
            "external_id": "777",
        }
        paths.append(request.url.path)
        return httpx.Response(204)

    api = build_api(handler)
    await api.clear_exercise_history(777, 9)
    await api.permanently_delete_exercise(777, 9)

    assert paths == [
        "/exercises/9/history",
        "/exercises/9/permanent",
    ]


@pytest.mark.asyncio
async def test_create_exercise_entry_maps_backend_conflict() -> None:
    api = build_api(lambda request: httpx.Response(409))

    with pytest.raises(ResourceConflictError):
        await api.create_exercise_entry(1, 9, [10], date.today())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (403, AccessForbiddenError),
        (404, ResourceNotFoundError),
        (500, UnexpectedApiError),
    ],
)
async def test_http_errors_are_mapped_to_domain_errors(
    status_code: int,
    expected_error: type[Exception],
) -> None:
    api = build_api(lambda request: httpx.Response(status_code))

    with pytest.raises(expected_error):
        await api.list_exercises(1)


@pytest.mark.asyncio
async def test_timeout_is_mapped_to_backend_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    api = build_api(handler)

    with pytest.raises(BackendUnavailableError):
        await api.resolve_user(1, "Europe/Moscow")


@pytest.mark.asyncio
async def test_invalid_backend_payload_is_mapped_to_unexpected_error() -> None:
    api = build_api(lambda request: httpx.Response(200, json={"id": 1}))

    with pytest.raises(UnexpectedApiError):
        await api.list_exercises(1)
