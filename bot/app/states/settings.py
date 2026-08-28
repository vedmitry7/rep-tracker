from aiogram.fsm.state import State, StatesGroup


class ChangeTimezone(StatesGroup):
    entering_timezone = State()
