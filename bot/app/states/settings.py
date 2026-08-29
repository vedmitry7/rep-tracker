from aiogram.fsm.state import State, StatesGroup


class ChangeTimezone(StatesGroup):
    entering_timezone = State()


class ImportData(StatesGroup):
    waiting_for_file = State()
    waiting_for_strategy = State()
    waiting_for_confirmation = State()
