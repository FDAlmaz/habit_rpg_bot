# модуль для PvP боёв
# тут вызов на битву, расчёт силы с учётом класса, награды
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import (
    get_conn as get_connection,
    get_pvp_power,
    can_pvp as can_pvp_battle,
    save_pvp_cd as save_pvp_cooldown,
    save_pvp_battle,
    add_exp as update_user_exp,
    add_skill_pts as add_skill_points,
    give_ach as award_achievement,
    get_user
)
from datetime import datetime
router = Router()
# главное меню PvP
@router.message(F.text == "PvP Арена")
async def pvp_menu(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    # создаём клавиатуру с двумя кнопками
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вызвать на битву", callback_data="challenge")],
        [InlineKeyboardButton(text="История битв", callback_data="history")]
    ])
    await msg.answer(
        "PVP АРЕНА\n\n"
        "Вызывай друзей на битву и докажи свою силу!\n\n"
        "Как это работает:\n"
        "- Твоя сила рассчитывается из навыков, уровня и класса\n"
        "- Бонусы классов: Воин +30% к Силе, Маг +30% к Интеллекту, Разбойник +30% к Ловкости\n"
        "- Победитель получает +50 XP и +1 очко навыка\n"
        "- Проигравший получает +25 XP\n"
        "- С одним игроком можно сражаться раз в день\n\n"
        "Выбери действие:",
        reply_markup=kb
    )
# меню вызова (инструкция)
@router.callback_query(F.data == "challenge")
async def challenge_menu(callback):
    await callback.message.edit_text(
        "ВЫЗОВ НА БИТВУ\n\n"
        "Введи username соперника командой:\n"
        "/fight @username\n\n"
        "Пример: /fight @durov"
    )
    await callback.answer()
# обработка команды /fight
@router.message(F.text.startswith('/fight'))
async def fight_challenge(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Использование: /fight @username")
        return
    target_uname = parts[1].lstrip('@')
    ch_id = msg.from_user.id
    ch_name = msg.from_user.first_name
    # ищем соперника в базе данных
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, first_name FROM users WHERE username = ?', (target_uname,))
    target = cur.fetchone()
    if not target:
        conn.close()
        await msg.answer(f"Пользователь @{target_uname} не найден. Убедись, что он зарегистрирован в боте.")
        return
    opp_id = target[0]
    opp_name = target[1]
    # достаём классы для отображения бонусов
    cur.execute('SELECT class_type FROM users WHERE user_id = ?', (ch_id,))
    ch_class = cur.fetchone()[0]
    cur.execute('SELECT class_type FROM users WHERE user_id = ?', (opp_id,))
    opp_class = cur.fetchone()[0]
    conn.close()
    if ch_id == opp_id:
        await msg.answer("Нельзя вызвать самого себя!")
        return
    # проверяем кулдаун (раз в день с одним игроком)
    ok, err_msg = can_pvp_battle(ch_id, opp_id)
    if not ok:
        await msg.answer(err_msg)
        return
    # считаем силу с бонусами класса
    ch_power, ch_bonus = get_pvp_power(ch_id)
    opp_power, opp_bonus = get_pvp_power(opp_id)
    # строка с бонусами классов для вывода
    bonus_line = (
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"БОНУСЫ КЛАССОВ:\n"
        f"- {ch_name} ({ch_class}): {ch_bonus}\n"
        f"- {opp_name} ({opp_class}): {opp_bonus}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
    )
    # определяем победителя
    if ch_power > opp_power:
        win_id = ch_id
        win_name = ch_name
        lose_id = opp_id
        lose_name = opp_name
        win_msg = f"ПОБЕДА!\n\nТвоя сила {ch_power} vs {opp_power} у соперника"
    elif opp_power > ch_power:
        win_id = opp_id
        win_name = opp_name
        lose_id = ch_id
        lose_name = ch_name
        win_msg = f"ПОРАЖЕНИЕ...\n\nСила соперника {opp_power} vs {ch_power} у тебя"
    else:
        # ничья - побеждает вызвавший
        win_id = ch_id
        win_name = ch_name
        lose_id = opp_id
        lose_name = opp_name
        win_msg = f"НИЧЬЯ!\n\nПо правилам арены победа присуждена вызвавшему!\nСила: {ch_power} vs {opp_power}"
    # сохраняем результат битвы в бд
    save_pvp_battle(ch_id, opp_id, ch_power, opp_power, win_id)
    save_pvp_cooldown(ch_id, opp_id)
    save_pvp_cooldown(opp_id, ch_id)
    # начисляем награды победителю и проигравшему
    if win_id == ch_id:
        update_user_exp(ch_id, 50, 0)      # победитель получает 50 XP
        add_skill_points(ch_id, 1)         # победитель получает очко навыка
        award_achievement(ch_id, 8)        # ачивка за первую победу
        update_user_exp(opp_id, 25, 0)     # проигравший получает 25 XP
        result_text = (
            f"РЕЗУЛЬТАТ БИТВЫ\n\n"
            f"{ch_name} vs {opp_name}\n"
            f"{bonus_line}"
            f"{win_msg}\n\n"
            f"НАГРАДЫ:\n"
            f"- {win_name}: +50 XP, +1 очко навыка\n"
            f"- {lose_name}: +25 XP\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"Сражайся снова завтра!"
        )
    else:
        update_user_exp(opp_id, 50, 0)
        add_skill_points(opp_id, 1)
        award_achievement(opp_id, 8)
        update_user_exp(ch_id, 25, 0)
        result_text = (
            f"РЕЗУЛЬТАТ БИТВЫ\n\n"
            f"{ch_name} vs {opp_name}\n"
            f"{bonus_line}"
            f"{win_msg}\n\n"
            f"НАГРАДЫ:\n"
            f"- {win_name}: +50 XP, +1 очко навыка\n"
            f"- {lose_name}: +25 XP\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"Сражайся снова завтра!"
        )
    await msg.answer(result_text)
    # отправляем результат сопернику
    try:
        await msg.bot.send_message(
            opp_id,
            f"БИТВА ЗАВЕРШЕНА!\n\n"
            f"{ch_name} вызвал тебя на битву!\n\n"
            f"{win_msg}\n\n"
            f"НАГРАДЫ:\n"
            f"- {'Ты' if win_id == opp_id else win_name}: +50 XP, +1 очко навыка\n"
            f"- {'Ты' if lose_id == opp_id else lose_name}: +25 XP"
        )
    except:
        pass
# история битв (последние 10)
@router.callback_query(F.data == "history")
async def battle_history(callback):
    uid = callback.from_user.id
    usr = get_user(uid)
    if not usr:
        await callback.message.edit_text("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        await callback.answer()
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT ch_id, opp_id, ch_power, opp_power, winner_id, battle_time
        FROM pvp_battles
        WHERE ch_id = ? OR opp_id = ?
        ORDER BY battle_time DESC
        LIMIT 10
    ''', (uid, uid))
    battles = cur.fetchall()
    conn.close()
    if not battles:
        await callback.message.edit_text(
            "ИСТОРИЯ БИТВ\n\n"
            "У тебя пока нет проведённых битв.\n"
            "Вызови друга на битву через /fight @username"
        )
        await callback.answer()
        return
    txt = "ИСТОРИЯ БИТВ\n\n"
    for b in battles:
        ch_id, opp_id, ch_pow, opp_pow, win_id, bt = b
        if win_id == uid:
            res = "ПОБЕДА"
        elif win_id == 0:
            res = "НИЧЬЯ"
        else:
            res = "ПОРАЖЕНИЕ"
        tm = datetime.fromisoformat(bt).strftime("%d.%m %H:%M")
        txt += f"- {tm} — {res} ({ch_pow} vs {opp_pow})\n"
    await callback.message.edit_text(txt)
    await callback.answer()