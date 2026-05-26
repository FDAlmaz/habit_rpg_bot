# модуль для отображения глобального рейтинга
# показывает топ-10 игроков по уровню и опыту
from aiogram import Router, F
from aiogram.types import Message
from database.database import get_top as get_top_users, get_user
router = Router()
# обработчик кнопки "Рейтинг"
@router.message(F.text == "Рейтинг")
async def show_rating(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    # получаем топ-10 пользователей из бд
    top = get_top_users(10)
    if not top:
        await msg.answer("Пока нет участников для рейтинга")
        return
    txt = "ТОП-10 ГЕРОЕВ\n\n"
    for i, u in enumerate(top, 1):
        # медальки для первых трёх мест
        if i == 1:
            medal = "🥇 "
        elif i == 2:
            medal = "🥈 "
        elif i == 3:
            medal = "🥉 "
        else:
            medal = f"{i}. "
        # u[0] - имя, u[1] - уровень, u[2] - опыт
        txt += f"{medal}{u[0]} — уровень {u[1]} ({u[2]} XP)\n"
    await msg.answer(txt)