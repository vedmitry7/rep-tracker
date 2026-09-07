from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.app.schemas.data_import import MAX_IMPORT_EXERCISES
from api.app.schemas.user import ExternalId, Provider


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId
    exercise_ids: Annotated[
        list[int], Field(min_length=1, max_length=MAX_IMPORT_EXERCISES)
    ]

    @field_validator("exercise_ids")
    @classmethod
    def validate_exercise_ids(cls, value: list[int]) -> list[int]:
        if any(exercise_id <= 0 for exercise_id in value):
            raise ValueError("exercise IDs must be positive")
        if len(value) != len(set(value)):
            raise ValueError("exercise IDs must be unique")
        return value
