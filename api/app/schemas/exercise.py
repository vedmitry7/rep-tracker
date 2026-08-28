from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from api.app.schemas.user import ExternalId, Provider


ExerciseName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class ExerciseIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId


class ExerciseCreateRequest(ExerciseIdentity):
    name: ExerciseName


class ExerciseUpdateRequest(ExerciseIdentity):
    name: ExerciseName


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    position: int
    is_archived: bool
    created_at: datetime
