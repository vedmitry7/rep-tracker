import logging
from datetime import date, datetime
from types import TracebackType

import httpx
from pydantic import BaseModel, ValidationError


logger = logging.getLogger(__name__)


class Exercise(BaseModel):
    id: int
    name: str


class ExerciseEntry(BaseModel):
    id: int
    exercise_id: int
    reps: list[int]
    performed_on: date
    created_at: datetime | None = None


class BestDay(BaseModel):
    date: date
    reps: int


class ExerciseStats(BaseModel):
    today: date
    total_reps: int
    today_reps: int
    last_7_days_reps: int
    last_30_days_reps: int
    all_time_entries: int
    active_days: int
    best_day: BestDay | None
    last_entry: ExerciseEntry | None

    @classmethod
    def empty(cls, *, today: date) -> "ExerciseStats":
        return cls(
            today=today,
            total_reps=0,
            today_reps=0,
            last_7_days_reps=0,
            last_30_days_reps=0,
            all_time_entries=0,
            active_days=0,
            best_day=None,
            last_entry=None,
        )


class ExerciseHistoryDay(BaseModel):
    date: date
    total_reps: int
    entries_count: int


class UserResolution(BaseModel):
    created: bool
    language: str


class UserSettings(BaseModel):
    timezone: str
    today: date
    language: str = "ru"


class ApiError(Exception):
    """Base exception safe for handlers to map to a user-facing message."""


class AccessForbiddenError(ApiError):
    pass


class ResourceNotFoundError(ApiError):
    pass


class ResourceConflictError(ApiError):
    pass


class BackendUnavailableError(ApiError):
    pass


class UnexpectedApiError(ApiError):
    pass


class InvalidRequestError(ApiError):
    pass


class RepTrackerApi:
    def __init__(
        self,
        base_url: str,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    async def __aenter__(self) -> "RepTrackerApi":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def resolve_user(
        self,
        telegram_user_id: int,
        default_timezone: str,
        default_language: str = "en",
    ) -> UserResolution:
        response = await self._request(
            "POST",
            "/users/resolve",
            json={
                **self._identity(telegram_user_id),
                "default_timezone": default_timezone,
                "default_language": default_language,
            },
            expected_statuses={200, 201},
        )
        try:
            language = response.json()["language"]
            return UserResolution(
                created=response.status_code == 201,
                language=language,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            logger.exception("Backend returned an invalid user resolution")
            raise UnexpectedApiError from error

    async def get_user_settings(self, telegram_user_id: int) -> UserSettings:
        response = await self._request(
            "GET",
            "/users/settings",
            params=self._identity(telegram_user_id),
            expected_statuses={200},
        )
        try:
            return UserSettings.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            logger.exception("Backend returned invalid user settings")
            raise UnexpectedApiError from error

    async def update_user_timezone(
        self,
        telegram_user_id: int,
        timezone: str,
    ) -> UserSettings:
        response = await self._request(
            "PATCH",
            "/users/settings",
            json={**self._identity(telegram_user_id), "timezone": timezone},
            expected_statuses={200},
        )
        try:
            return UserSettings.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            logger.exception("Backend returned invalid user settings")
            raise UnexpectedApiError from error

    async def update_user_language(
        self,
        telegram_user_id: int,
        language: str,
    ) -> UserSettings:
        response = await self._request(
            "PATCH",
            "/users/settings",
            json={**self._identity(telegram_user_id), "language": language},
            expected_statuses={200},
        )
        try:
            return UserSettings.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            logger.exception("Backend returned invalid user settings")
            raise UnexpectedApiError from error

    async def list_exercises(self, telegram_user_id: int) -> list[Exercise]:
        response = await self._request(
            "GET",
            "/exercises",
            params=self._identity(telegram_user_id),
            expected_statuses={200},
        )
        try:
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("Exercise response is not a list")
            return [Exercise.model_validate(item) for item in payload]
        except (TypeError, ValueError, ValidationError) as error:
            logger.exception("Backend returned an invalid exercise list")
            raise UnexpectedApiError from error

    async def create_exercise(
        self,
        telegram_user_id: int,
        name: str,
    ) -> Exercise:
        response = await self._request(
            "POST",
            "/exercises",
            json={**self._identity(telegram_user_id), "name": name},
            expected_statuses={201},
        )
        try:
            return Exercise.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            logger.exception("Backend returned an invalid exercise")
            raise UnexpectedApiError from error

    async def create_exercise_entry(
        self,
        telegram_user_id: int,
        exercise_id: int,
        reps: list[int],
        performed_on: date,
    ) -> ExerciseEntry:
        response = await self._request(
            "POST",
            "/exercise-entries",
            json={
                **self._identity(telegram_user_id),
                "exercise_id": exercise_id,
                "reps": reps,
                "performed_on": performed_on.isoformat(),
            },
            expected_statuses={201},
        )
        try:
            return ExerciseEntry.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            logger.exception("Backend returned an invalid exercise entry")
            raise UnexpectedApiError from error

    async def get_exercise_stats(
        self,
        telegram_user_id: int,
        exercise_id: int,
    ) -> ExerciseStats:
        response = await self._request(
            "GET",
            f"/exercises/{exercise_id}/stats",
            params=self._identity(telegram_user_id),
            expected_statuses={200},
        )
        try:
            return ExerciseStats.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            logger.exception("Backend returned invalid exercise statistics")
            raise UnexpectedApiError from error

    async def get_exercise_entries(
        self,
        telegram_user_id: int,
        exercise_id: int,
        *,
        limit: int = 10,
        offset: int = 0,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ExerciseEntry]:
        params: dict[str, str | int] = {
            **self._identity(telegram_user_id),
            "limit": limit,
            "offset": offset,
        }
        if from_date is not None:
            params["from"] = from_date.isoformat()
        if to_date is not None:
            params["to"] = to_date.isoformat()
        response = await self._request(
            "GET",
            f"/exercises/{exercise_id}/entries",
            params=params,
            expected_statuses={200},
        )
        try:
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("Exercise entries response is not a list")
            return [ExerciseEntry.model_validate(item) for item in payload]
        except (TypeError, ValueError, ValidationError) as error:
            logger.exception("Backend returned an invalid exercise entry list")
            raise UnexpectedApiError from error

    async def get_exercise_history_days(
        self,
        telegram_user_id: int,
        exercise_id: int,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ExerciseHistoryDay]:
        response = await self._request(
            "GET",
            f"/exercises/{exercise_id}/history-days",
            params={
                **self._identity(telegram_user_id),
                "limit": limit,
                "offset": offset,
            },
            expected_statuses={200},
        )
        try:
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("Exercise history days response is not a list")
            return [ExerciseHistoryDay.model_validate(item) for item in payload]
        except (TypeError, ValueError, ValidationError) as error:
            logger.exception("Backend returned an invalid history days list")
            raise UnexpectedApiError from error

    async def update_exercise_entry(
        self,
        telegram_user_id: int,
        entry_id: int,
        *,
        reps: list[int] | None = None,
        performed_on: date | None = None,
    ) -> ExerciseEntry:
        payload: dict[str, object] = self._identity(telegram_user_id)
        if reps is not None:
            payload["reps"] = reps
        if performed_on is not None:
            payload["performed_on"] = performed_on.isoformat()
        response = await self._request(
            "PATCH",
            f"/exercise-entries/{entry_id}",
            json=payload,
            expected_statuses={200},
        )
        try:
            return ExerciseEntry.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            logger.exception("Backend returned an invalid updated exercise entry")
            raise UnexpectedApiError from error

    async def delete_exercise_entry(
        self,
        telegram_user_id: int,
        entry_id: int,
    ) -> None:
        await self._request(
            "DELETE",
            f"/exercise-entries/{entry_id}",
            params=self._identity(telegram_user_id),
            expected_statuses={204},
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        expected_statuses: set[int],
        **kwargs: object,
    ) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as error:
            logger.warning("Backend request timed out: %s %s", method, path)
            raise BackendUnavailableError from error
        except httpx.RequestError as error:
            logger.warning("Backend request failed: %s %s", method, path, exc_info=True)
            raise BackendUnavailableError from error

        if response.status_code == 403:
            raise AccessForbiddenError
        if response.status_code == 404:
            raise ResourceNotFoundError
        if response.status_code == 409:
            raise ResourceConflictError
        if response.status_code == 422:
            raise InvalidRequestError
        if response.status_code not in expected_statuses:
            logger.error(
                "Unexpected backend response: %s %s returned %s",
                method,
                path,
                response.status_code,
            )
            raise UnexpectedApiError

        return response

    @staticmethod
    def _identity(telegram_user_id: int) -> dict[str, str]:
        return {
            "provider": "telegram",
            "external_id": str(telegram_user_id),
        }
