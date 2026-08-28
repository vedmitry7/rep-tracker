from datetime import date

from pydantic import BaseModel, ConfigDict


class ExerciseHistoryDayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    total_reps: int
    entries_count: int
