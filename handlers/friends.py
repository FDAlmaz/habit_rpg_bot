# модуль для работы с друзьями
# тут добавление, принятие заявок, просмотр друзей и рейтинг
from aiogram import Router, F
from aiogram.types import Message
from database.database import (
    send_friend_req as add_friend_request,
    accept_friend as accept_friend_request,
    get_friends_list as get_friends,
    get_pending as get_pending_requests,
    get_friends_rank as get_friends_rating,
    get_user
)
# создаём роутер
router = Router()
# рейтинг среди друзей
@router.message(F.text == "Рейтинг")
async def show_friends_rating(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    rating = get_friends_rating(uid)
    if not rating:
        await msg.answer(
            "РЕЙТИНГ СРЕДИ ДРУЗЕЙ\n\n"
            "Рейтинг показывается только среди друзей.\n"
            "Добавь друга через команду /add_friend @username\n\n"
            "У тебя пока нет друзей, поэтому рейтинг пуст."
        )
        return
    txt = "РЕЙТИНГ СРЕДИ ДРУЗЕЙ\n\n"
    for i, f in enumerate(rating, 1):
        # берём имя, если нет то юзернейм, если нет то айди
        nm = f[2] or f[1] or f"User_{f[0]}"
        if f[0] == uid:
            txt += f"{i}. {nm} (это ты) — уровень {f[3]} ({f[4]} XP)\n"
        else:
            txt += f"{i}. {nm} — уровень {f[3]} ({f[4]} XP)\n"
    await msg.answer(txt)
# список друзей и входящие заявки
@router.message(F.text == "Друзья")
async def show_friends(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    friends = get_friends(uid)
    requests = get_pending_requests(uid)
    txt = "ТВОИ ДРУЗЬЯ\n\n"
    if not friends and not requests:
        txt += "У тебя пока нет друзей.\n\n"
        txt += "Как добавить друга:\n"
        txt += "1. Узнай username друга (например, @durov)\n"
        txt += "2. Отправь команду: /add_friend @username\n"
        txt += "3. Друг должен принять заявку: /accept @твой_username"
    else:
        if friends:
            txt += "Твои друзья:\n"
            for f in friends:
                nm = f[2] or f[1] or f"User_{f[0]}"
                txt += f"- {nm} (уровень {f[3]}, {f[4]} XP)\n"
            txt += "\n"
        if requests:
            txt += "Входящие заявки:\n"
            for rq in requests:
                nm = rq[1] or rq[0]
                txt += f"- от {nm} — принять: /accept {rq[0]}\n"
            txt += "\n"
        txt += "Добавить друга: /add_friend @username"
    await msg.answer(txt)
# отправить заявку в друзья
@router.message(F.text.startswith('/add_friend'))
async def add_friend(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Использование: /add_friend @username\nПример: /add_friend @durov")
        return
    uname = parts[1].lstrip('@')
    req_name = msg.from_user.first_name
    ok, res = add_friend_request(uid, uname, req_name)
    await msg.answer(res)
# принять заявку в друзья
@router.message(F.text.startswith('/accept'))
async def accept_friend(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Использование: /accept @username\nПример: /accept @durov")
        return
    uname = parts[1].lstrip('@')
    ok, res = accept_friend_request(uid, uname)
    await msg.answer(res)