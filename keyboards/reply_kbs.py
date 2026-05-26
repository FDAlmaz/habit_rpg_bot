from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
def main_keyboard():
    buttons = [
        [KeyboardButton(text="Мои привычки")],
        [KeyboardButton(text="Мой профиль")],
        [KeyboardButton(text="Создать привычку")],
        [KeyboardButton(text="Рейтинг"), KeyboardButton(text="Друзья")],
        [KeyboardButton(text="Мои ачивки")],
        [KeyboardButton(text="Распределить очки")],
        [KeyboardButton(text="PvP Арена")],
        [KeyboardButton(text="Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
def cancel_keyboard():
    button = [[KeyboardButton(text="Отмена")]]
    return ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)
def back_cancel_keyboard():
    buttons = [[KeyboardButton(text="Назад"), KeyboardButton(text="Отмена")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
def habit_action_keyboard(habit_id):
    """Клавиатура для действий с привычкой"""
    buttons = [
        [
            KeyboardButton(text=f"Выполнить {habit_id}"),
            KeyboardButton(text=f"Удалить {habit_id}")
        ],
        [KeyboardButton(text="Назад к списку")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)