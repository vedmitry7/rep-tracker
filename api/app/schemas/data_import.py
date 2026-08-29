import re
from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from api.app.core.exercise_names import normalize_exercise_name
from api.app.schemas.exercise import ExerciseName
from api.app.schemas.exercise_entry import Reps
from api.app.schemas.user import ExternalId, Provider


MAX_IMPORT_EXERCISES = 500
MAX_IMPORT_DAYS_PER_EXERCISE = 5_000
MAX_IMPORT_ENTRIES = 50_000


class ImportStrategy(StrEnum):
    MERGE = "merge"
    REPLACE = "replace"


class ImportDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    entries: Annotated[list[Reps], Field(min_length=1)]

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, value: object) -> object:
        if (
            not isinstance(value, str)
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None
        ):
            raise ValueError("date must use YYYY-MM-DD")
        return value


class ImportExercise(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ExerciseName
    days: Annotated[
        list[ImportDay],
        Field(min_length=1, max_length=MAX_IMPORT_DAYS_PER_EXERCISE),
    ]


class ImportDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(strict=True)
    exercises: Annotated[
        list[ImportExercise],
        Field(min_length=1, max_length=MAX_IMPORT_EXERCISES),
    ]

    @model_validator(mode="after")
    def validate_document(self) -> "ImportDocument":
        if self.version != 1:
            raise ValueError("version must be 1")
        entries_count = sum(
            len(day.entries)
            for exercise in self.exercises
            for day in exercise.days
        )
        if entries_count > MAX_IMPORT_ENTRIES:
            raise ValueError(
                f"import cannot contain more than {MAX_IMPORT_ENTRIES} entries"
            )
        normalized_names = [
            normalize_exercise_name(exercise.name) for exercise in self.exercises
        ]
        if len(normalized_names) != len(set(normalized_names)):
            raise ValueError(
                "import cannot contain duplicate normalized exercise names"
            )
        return self


class ImportIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId
    document: ImportDocument


class ImportApplyRequest(ImportIdentity):
    strategy: ImportStrategy


class ImportPreviewResponse(BaseModel):
    exercises_count: int
    entries_count: int
    total_reps: int
    date_from: date
    date_to: date
    new_exercises: list[str]
    existing_exercises: list[str]


class ImportResultResponse(BaseModel):
    strategy: ImportStrategy
    exercises_created: int
    existing_exercises_updated: int
    entries_imported: int
    total_reps_imported: int
