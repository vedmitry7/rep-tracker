from aiogram.fsm.state import State, StatesGroup


class AddResult(StatesGroup):
    entering_result = State()
    choosing_date = State()
    entering_date = State()
    constructor = State()
