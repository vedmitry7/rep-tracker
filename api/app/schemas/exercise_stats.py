from datetime import date

from pydantic import BaseModel, ConfigDict

from api.app.schemas.exercise_entry import ExerciseEntryResponse


class BestDayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    reps: int


class ExerciseStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_reps: int
    today_reps: int
    last_7_days_reps: int
    last_30_days_reps: int
    all_time_entries: int
    active_days: int
    best_day: BestDayResponse | None
    last_entry: ExerciseEntryResponse | None
    today: date
