from aiogram.fsm.state import State, StatesGroup
class HabitForm(StatesGroup):
    name = State()
    description = State()
    difficulty = State()
    periodicity_unit = State()  # новая: день/неделя/месяц
    periodicity_value = State()  # новая: количество