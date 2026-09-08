from aiogram.fsm.state import State, StatesGroup


class Support(StatesGroup):
    confirming_terms = State()
    entering_amount = State()
