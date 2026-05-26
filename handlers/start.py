# модуль для обработки команды /start
# тут регистрация нового пользователя и выбор класса
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import register_user, get_user, update_user_class
from keyboards.reply_kbs import main_keyboard
router = Router()
# клавиатура выбора класса
def class_kb():
    btns = [
        [InlineKeyboardButton(text="Воин", callback_data="cl_war")],
        [InlineKeyboardButton(text="Маг", callback_data="cl_mage")],
        [InlineKeyboardButton(text="Разбойник", callback_data="cl_rog")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)
# обработчик команды /start
@router.message(Command("start"))
async def cmd_start(msg: Message):
    uid = msg.from_user.id
    uname = msg.from_user.username
    fname = msg.from_user.first_name
    # регистрируем пользователя в бд (если ещё нет)
    register_user(uid, uname, fname)
    usr = get_user(uid)
    # индекс 10 - это class_type в кортеже пользователя
    if usr and len(usr) > 10 and usr[10] and usr[10] != 'Новичок':
        # у пользователя уже есть класс
        await msg.answer(
            f"С возвращением, {fname}!\n\n"
            f"Твой класс: {usr[10]}\n\n"
            f"Выполняй привычки, повышай уровень и прокачивай персонажа!",
            reply_markup=main_keyboard()
        )
    else:
        # новый пользователь - предлагаем выбрать класс
        await msg.answer(
            f"Привет, {fname}!\n\n"
            "Добро пожаловать в RPG-трекер привычек!\n\n"
            "Выбери свой класс. От этого зависит внешний вид твоего персонажа:\n\n"
            "Воин — для тех, кто выбирает дисциплину и силу\n"
            "Маг — для тех, кто стремится к знаниям и мудрости\n"
            "Разбойник — для тех, кто ценит ловкость и хитрость\n\n"
            "Какой класс выберешь?",
            reply_markup=class_kb()
        )
# выбор класса
@router.callback_query(F.data.startswith("cl_"))
async def select_class(cb):
    uid = cb.from_user.id
    # маппинг callback_data на название класса
    class_map = {
        "cl_war": "Воин",
        "cl_mage": "Маг",
        "cl_rog": "Разбойник"
    }
    cls = class_map.get(cb.data, "Новичок")
    # сохраняем класс в бд
    update_user_class(uid, cls)
    await cb.message.edit_text(
        f"Ты выбрал класс: {cls}!\n\n"
        f"Теперь создавай привычки, выполняй их и прокачивай своего персонажа.\n"
        f"Чем выше уровень, тем круче будет выглядеть твой герой!\n\n"
        f"Используй кнопки меню ниже"
    )
    await cb.message.answer(
        "Поехали!",
        reply_markup=main_keyboard()
    )
    await cb.answer()