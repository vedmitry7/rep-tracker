from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, ExerciseEntry, User


@pytest.mark.parametrize(
    "reps",
    [[10], [10, 10, 10, 10], [10, 9, 8, 7]],
)
def test_exercise_entry_accepts_positive_reps(reps: list[int]) -> None:
    performed_on = date(2026, 8, 27)
    entry = ExerciseEntry(
        exercise_id=1,
        reps=reps,
        performed_on=performed_on,
    )

    assert entry.reps == reps
    assert entry.performed_on == performed_on


@pytest.mark.parametrize(
    "reps",
    [[], [0], [-1], [10, 0], [True], None],
)
def test_exercise_entry_rejects_invalid_reps(reps: object) -> None:
    with pytest.raises(ValueError):
        ExerciseEntry(
            exercise_id=1,
            reps=reps,
            performed_on=date(2026, 8, 27),
        )


@pytest.mark.asyncio
async def test_exercise_entry_persists_integer_array(
    db_session: AsyncSession,
) -> None:
    async with db_session.begin():
        user = User()
        exercise = Exercise(name="Pull-ups")
        exercise.exercise_entries.append(
            ExerciseEntry(
                reps=[10, 9, 8, 7],
                performed_on=date(2026, 8, 26),
            )
        )
        user.exercises.append(exercise)
        db_session.add(user)
        await db_session.flush()
        entry_id = exercise.exercise_entries[0].id

    stored_entry = await db_session.scalar(
        select(ExerciseEntry).where(ExerciseEntry.id == entry_id)
    )

    assert stored_entry is not None
    assert stored_entry.reps == [10, 9, 8, 7]
    assert stored_entry.performed_on == date(2026, 8, 26)
    assert stored_entry.exercise_id == exercise.id
