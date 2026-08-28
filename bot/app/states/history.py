from aiogram.fsm.state import State, StatesGroup


class EditHistoryEntry(StatesGroup):
    editing_reps = State()
    choosing_date = State()
    entering_date = State()
