# модуль для распределения очков навыков
# тут можно улучшить силу, интеллект или ловкость
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import get_stats as get_user_skills, upgrade_stat as upgrade_skill, get_user
router = Router()
# главное меню прокачки
@router.message(F.text == "Распределить очки")
async def show_upgrade_menu(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    skills = get_user_skills(uid)  # (сила, интеллект, ловкость, очки_навыков)
    if not skills:
        await msg.answer("Ошибка получения данных")
        return
    pts = skills[3] if len(skills) > 3 else 0
    st = skills[0]
    it = skills[1]
    ag = skills[2]
    if pts == 0:
        await msg.answer(
            "У тебя нет очков навыков!\n\n"
            "Как получить очки навыков?\n"
            "За каждый новый уровень ты получаешь 1 очко навыков.\n"
            "Выполняй привычки, чтобы повышать уровень!"
        )
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Сила ({st}) +1", callback_data="up_str")],
        [InlineKeyboardButton(text=f"Интеллект ({it}) +1", callback_data="up_int")],
        [InlineKeyboardButton(text=f"Ловкость ({ag}) +1", callback_data="up_agi")],
        [InlineKeyboardButton(text="Закрыть", callback_data="close_up")]
    ])
    await msg.answer(
        f"РАСПРЕДЕЛЕНИЕ ОЧКОВ НАВЫКОВ\n\n"
        f"Доступно очков: {pts}\n\n"
        f"Выбери навык для улучшения:\n\n"
        f"Сила — увеличивает урон в соревнованиях\n"
        f"Интеллект — ускоряет получение ачивок\n"
        f"Ловкость — повышает шанс критического удара\n\n"
        f"Нажми на кнопку с навыком, чтобы улучшить его.",
        reply_markup=kb
    )
# обработка улучшения навыка
@router.callback_query(F.data.startswith("up_"))
async def upgrade_skill_callback(cb):
    uid = cb.from_user.id
    usr = get_user(uid)
    if not usr:
        await cb.message.edit_text("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        await cb.answer()
        return
    # маппинг callback_data на название навыка
    skill_map = {
        "up_str": "сила",
        "up_int": "интеллект",
        "up_agi": "ловкость"
    }
    sk = skill_map.get(cb.data)
    if not sk:
        await cb.answer("Неизвестный навык")
        return
    ok, res = upgrade_skill(uid, sk)
    if ok:
        skills = get_user_skills(uid)
        if skills:
            pts = skills[3] if len(skills) > 3 else 0
            st = skills[0]
            it = skills[1]
            ag = skills[2]
            if pts > 0:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"Сила ({st}) +1", callback_data="up_str")],
                    [InlineKeyboardButton(text=f"Интеллект ({it}) +1", callback_data="up_int")],
                    [InlineKeyboardButton(text=f"Ловкость ({ag}) +1", callback_data="up_agi")],
                    [InlineKeyboardButton(text="Закрыть", callback_data="close_up")]
                ])
                await cb.message.edit_text(
                    f"РАСПРЕДЕЛЕНИЕ ОЧКОВ НАВЫКОВ\n\n"
                    f"Доступно очков: {pts}\n\n"
                    f"{res}\n\n"
                    f"Продолжай улучшать навыки:",
                    reply_markup=kb
                )
            else:
                await cb.message.edit_text(
                    f"РАСПРЕДЕЛЕНИЕ ОЧКОВ НАВЫКОВ\n\n"
                    f"{res}\n\n"
                    f"Ты использовал все очки навыков!\n"
                    f"Повышай уровень, чтобы получить новые очки."
                )
        else:
            await cb.message.edit_text(res)
    else:
        await cb.answer(res, show_alert=True)
    await cb.answer()
# закрыть меню прокачки
@router.callback_query(F.data == "close_up")
async def close_upgrade(cb):
    await cb.message.delete()
    await cb.answer()