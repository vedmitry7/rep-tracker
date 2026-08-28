from aiogram.fsm.state import State, StatesGroup


class CreateExercise(StatesGroup):
    waiting_for_name = State()
