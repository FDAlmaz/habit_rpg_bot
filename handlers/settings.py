# модуль для настроек аккаунта
# тут можно удалить свой аккаунт со всеми данными
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import del_account as delete_user_account, get_user
from keyboards.reply_kbs import main_keyboard
router = Router()
# главное меню настроек
@router.message(F.text == "Настройки")
async def settings_menu(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить аккаунт", callback_data="del_acc")],
        [InlineKeyboardButton(text="Назад", callback_data="back_main")]
    ])
    await msg.answer(
        "НАСТРОЙКИ\n\n"
        "Здесь ты можешь управлять своим аккаунтом.\n\n"
        "ВНИМАНИЕ! Удаление аккаунта приведёт к потере:\n"
        "- всех привычек\n"
        "- прогресса и уровня\n"
        "- ачивок\n"
        "- друзей и рейтинга\n\n"
        "Восстановить данные будет невозможно!",
        reply_markup=kb
    )
# подтверждение удаления
@router.callback_query(F.data == "del_acc")
async def confirm_delete(cb: CallbackQuery):
    uid = cb.from_user.id
    usr = get_user(uid)
    if not usr:
        await cb.message.edit_text("Аккаунт не найден. Напиши /start")
        await cb.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, удалить навсегда", callback_data="confirm_del")],
        [InlineKeyboardButton(text="Отмена", callback_data="back_set")]
    ])
    await cb.message.edit_text(
        "ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ\n\n"
        "Ты действительно хочешь удалить свой аккаунт?\n\n"
        "Все данные будут потеряны без возможности восстановления.\n\n"
        "Если ты уверен, нажми кнопку ниже.",
        reply_markup=kb
    )
    await cb.answer()
# окончательное удаление
@router.callback_query(F.data == "confirm_del")
async def delete_account(cb: CallbackQuery):
    uid = cb.from_user.id
    usr = get_user(uid)
    if not usr:
        await cb.message.edit_text("Аккаунт не найден. Напиши /start")
        await cb.answer()
        return
    ok, msg = delete_user_account(uid)
    if ok:
        await cb.message.edit_text(
            "АККАУНТ УДАЛЁН\n\n"
            "Твой аккаунт и все данные удалены.\n\n"
            "Если захочешь вернуться, просто напиши /start — мы создадим нового персонажа!\n\n"
            "Будем ждать тебя снова!"
        )
        await cb.bot.send_message(uid, "Твой аккаунт удалён. Чтобы начать заново, напиши /start")
    else:
        await cb.message.edit_text(f"Ошибка при удалении: {msg}\n\nПопробуй позже или обратись к администратору.")
    await cb.answer()
# возврат в меню настроек
@router.callback_query(F.data == "back_set")
async def back_to_settings(cb: CallbackQuery):
    uid = cb.from_user.id
    usr = get_user(uid)
    if not usr:
        await cb.message.edit_text("Аккаунт не найден. Напиши /start")
        await cb.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить аккаунт", callback_data="del_acc")],
        [InlineKeyboardButton(text="Назад", callback_data="back_main")]
    ])
    await cb.message.edit_text(
        "НАСТРОЙКИ\n\n"
        "Здесь ты можешь управлять своим аккаунтом.\n\n"
        "ВНИМАНИЕ! Удаление аккаунта приведёт к потере всех данных!",
        reply_markup=kb
    )
    await cb.answer()
# возврат в главное меню
@router.callback_query(F.data == "back_main")
async def back_to_main(cb: CallbackQuery):
    await cb.message.delete()
    await cb.message.answer("Возврат в главное меню", reply_markup=main_keyboard())
    await cb.answer()