# модуль для работы с ачивками
# тут пользователь может посмотреть свои достижения и список всех возможных
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import get_user_achs as get_user_achievements, get_all_achs_with_progress as get_all_achievements_with_progress, get_user
# создаём роутер
router = Router()
# главное меню ачивок
@router.message(F.text == "Мои ачивки")
async def ach_menu(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    # клавиатура с двумя кнопками
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои полученные ачивки", callback_data="my_ach")],
        [InlineKeyboardButton(text="Все ачивки и как получить", callback_data="all_ach")]
    ])
    await msg.answer(
        "СИСТЕМА АЧИВОК\n\n"
        "Выбери, что хочешь посмотреть:",
        reply_markup=kb
    )
# показывает только полученные ачивки
@router.callback_query(F.data == "my_ach")
async def show_my_ach(callback):
    uid = callback.from_user.id
    usr = get_user(uid)
    if not usr:
        await callback.message.edit_text("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        await callback.answer()
        return
    achs = get_user_achievements(uid)
    if not achs:
        await callback.message.edit_text(
            "ТВОИ ДОСТИЖЕНИЯ\n\n"
            "У тебя пока нет ачивок.\n"
            "Как получить первую ачивку?\n"
            "Создай свою первую привычку!\n"
            "Используй кнопку 'Создать привычку' в главном меню."
        )
        await callback.answer()
        return
    out = "ТВОИ ДОСТИЖЕНИЯ\n\n"
    for a in achs:
        out += f" {a[0]}\n"
        out += f"   {a[1]}\n\n"
    out += "\nЧтобы увидеть все возможные ачивки, выбери 'Все ачивки' в меню."
    await callback.message.edit_text(out)
    await callback.answer()
# показывает все ачивки с прогрессом
@router.callback_query(F.data == "all_ach")
async def show_all_ach(callback):
    uid = callback.from_user.id
    usr = get_user(uid)
    if not usr:
        await callback.message.edit_text("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        await callback.answer()
        return
    achs = get_all_achievements_with_progress(uid)
    out = "ВСЕ АЧИВКИ\n\n"
    out += "Вот список всех достижений, которые можно получить:\n\n"
    for a in achs:
        if a['earned']:
            status = "ПОЛУЧЕНО"
        else:
            status = f"Прогресс: {a['current']}/{a['required']}"
        out += f"{a['name']}\n"
        out += f"   {a['descr']}\n"   # здесь было 'description', исправил на 'descr'
        out += f"   {status}\n\n"
    out += "\nПродолжай выполнять привычки, чтобы открыть все ачивки!"
    # кнопка назад
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к меню", callback_data="back_to_ach_menu")]
    ])
    await callback.message.edit_text(out, reply_markup=kb)
    await callback.answer()
# возврат в главное меню ачивок
@router.callback_query(F.data == "back_to_ach_menu")
async def back_to_ach_menu(callback):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мои полученные ачивки", callback_data="my_ach")],
        [InlineKeyboardButton(text="Все ачивки и как получить", callback_data="all_ach")]
    ])
    await callback.message.edit_text(
        "СИСТЕМА АЧИВОК\n\n"
        "Выбери, что хочешь посмотреть:",
        reply_markup=kb
    )
    await callback.answer()