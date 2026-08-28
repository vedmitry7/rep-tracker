from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.app.schemas.user import ExternalId, Provider


MAX_SETS_PER_ENTRY = 100
MAX_REPETITIONS_PER_SET = 10_000

Repetitions = Annotated[
    int,
    Field(strict=True, ge=1, le=MAX_REPETITIONS_PER_SET),
]
Reps = Annotated[
    list[Repetitions],
    Field(min_length=1, max_length=MAX_SETS_PER_ENTRY),
]


class ExerciseEntryIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId


class ExerciseEntryCreateRequest(ExerciseEntryIdentity):
    exercise_id: int = Field(gt=0)
    reps: Reps
    performed_on: date

class ExerciseEntryUpdateRequest(ExerciseEntryIdentity):
    reps: Reps | None = None
    performed_on: date | None = None

    @model_validator(mode="after")
    def validate_update(self) -> Self:
        changed_fields = self.model_fields_set - {"provider", "external_id"}
        if not changed_fields:
            raise ValueError("at least one field must be provided")
        if self.reps is None and "reps" in changed_fields:
            raise ValueError("reps cannot be null")
        if self.performed_on is None and "performed_on" in changed_fields:
            raise ValueError("performed_on cannot be null")
        return self


class ExerciseEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    reps: list[int]
    performed_on: date
    created_at: datetime
