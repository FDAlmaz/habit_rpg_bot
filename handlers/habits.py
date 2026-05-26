# модуль для обработки привычек
# тут вся основная логика работы с привычками пользователя
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from FSM import HabitForm
from database.database import (
    add_habit, get_habits as get_user_habits, del_habit as delete_habit,
    add_exp as update_user_exp, log_habit_done as log_habit_completion, get_user,
    give_ach as award_achievement, get_conn as get_connection, can_do_habit as can_complete_habit,
    reset_habit_counter
)
from keyboards.reply_kbs import main_keyboard
from datetime import datetime, timedelta
import re

# создаём роутер для обработки команд
router = Router()
# словарь с опытом за разную сложность
xp_for_difficulty = {
    'легко': 10,
    'средне': 25,
    'сложно': 50
}
# КЛАВИАТУРЫ
# клава с одной кнопкой "Отмена"
def cancel_kb():
    btn = [[KeyboardButton(text="Отмена")]]
    return ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
# клава с кнопками "Назад" и "Отмена"
def back_cancel_kb():
    btns = [[KeyboardButton(text="Назад"), KeyboardButton(text="Отмена")]]
    return ReplyKeyboardMarkup(keyboard=btns, resize_keyboard=True)
# инлайн-клава для выбора периода
def period_inline_kb():
    btns = [
        [InlineKeyboardButton(text="День", callback_data="unit_day")],
        [InlineKeyboardButton(text="Месяц", callback_data="unit_month")],
        [InlineKeyboardButton(text="Год", callback_data="unit_year")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)
# форматирует серию (просто число, без текста)
def fmt_streak(val, period_str):
    return str(val)
# ОСНОВНЫЕ ОБРАБОТЧИКИ
# показать список привычек пользователя
@router.message(lambda msg: msg.text == "Мои привычки")
async def show_my_habits(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)
    # если нет аккаунта
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    # получаем привычки из бд
    habits_list = get_user_habits(uid)
    if not habits_list:
        await msg.answer(
            "У тебя пока нет привычек.\n"
            "Создай первую через кнопку 'Создать привычку'",
            reply_markup=main_keyboard()
        )
        return
    # формируем текст для вывода
    out_text = "Твои привычки:\n\n"
    for h in habits_list:
        # достаём данные
        h_id, h_name, h_desc, h_diff, h_period, cur_streak, best_streak = h
        cur_str = fmt_streak(cur_streak, h_period)
        best_str = fmt_streak(best_streak, h_period)
        # проверяем, можно ли выполнить привычку сейчас
        wait_txt, can_do_now, period_days = can_complete_habit(h_id, uid)
        icon = "✓" if can_do_now else "⏰"
        info_txt = f" {wait_txt}" if wait_txt and not can_do_now else ""
        out_text += f"{icon} {h_name}{info_txt}\n"
        out_text += f"  Сложность: {h_diff}\n"
        out_text += f"  Периодичность: {h_period}\n"
        out_text += f"  Текущая серия: {cur_str}\n"
        out_text += f"  Рекорд: {best_str}\n\n"
    out_text += "Выбери привычку и действие:"
    # создаём кнопки для каждой привычки
    btns = []
    for h in habits_list:
        _, can_do_now, _ = can_complete_habit(h[0], uid)
        if can_do_now:
            btns.append([KeyboardButton(text=f"Выполнить {h[0]}"), KeyboardButton(text=f"Удалить {h[0]}")])
        else:
            btns.append([KeyboardButton(text=f"Скоро {h[0]}"), KeyboardButton(text=f"Удалить {h[0]}")])
    btns.append([KeyboardButton(text="Главное меню")])

    kb = ReplyKeyboardMarkup(keyboard=btns, resize_keyboard=True)
    await msg.answer(out_text, parse_mode="Markdown", reply_markup=kb)
# обработчик нажатия на кнопку "Выполнить"
@router.message(lambda msg: msg.text and msg.text.startswith("Выполнить"))
async def do_habit(msg: Message):
    try:
        uid = msg.from_user.id
        usr = get_user(uid)
        if not usr:
            await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
            return
        # достаём id привычки из текста кнопки
        nums = re.findall(r'\d+', msg.text)
        if not nums:
            await msg.answer("Не удалось определить ID привычки", reply_markup=main_keyboard())
            return
        hid = int(nums[0])
        # проверяем, можно ли выполнить
        wait_txt, can_do_now, period_days = can_complete_habit(hid, uid)
        if not can_do_now:
            await msg.answer(
                f"Эту привычку нельзя выполнить сейчас!\n\n"
                f"{wait_txt}\n\n"
                f"Периодичность: раз в {period_days} дней.",
                reply_markup=main_keyboard()
            )
            return
        # получаем привычку из бд
        habits_list = get_user_habits(uid)
        target_habit = None
        for h in habits_list:
            if h[0] == hid:
                target_habit = h
                break
        if not target_habit:
            await msg.answer("Привычка не найдена", reply_markup=main_keyboard())
            return
        # начисляем опыт
        gained_xp = xp_for_difficulty[target_habit[3]]
        new_streak, bonus_xp = log_habit_completion(hid, uid, gained_xp)
        if new_streak == -1:
            await msg.answer(
                f"Эту привычку нельзя выполнить сейчас!\n\n"
                f"Периодичность: раз в {period_days} дней.",
                reply_markup=main_keyboard()
            )
            return
        lvl_up = update_user_exp(uid, gained_xp, bonus_xp)
        # проверяем ачивку "Старатель" (10 выполнений)
        con = get_connection()
        cur = con.cursor()
        cur.execute('SELECT COUNT(*) FROM habit_logs WHERE user_id = ?', (uid,))
        compl_cnt = cur.fetchone()[0]
        con.close()
        if compl_cnt >= 10:
            award_achievement(uid, 2)
        # форматируем ответ
        streak_txt = fmt_streak(new_streak, target_habit[4])
        total_xp = gained_xp + bonus_xp
        resp = f"Выполнено: {target_habit[1]}!\n\n"
        resp += f"Базовый опыт: +{gained_xp} XP\n"
        resp += f"Бонус за серию: +{bonus_xp} XP\n"
        resp += f"Всего получено: +{total_xp} XP\n"
        resp += f"Текущая серия: {streak_txt}"
        if lvl_up:
            usr_data = get_user(uid)
            resp += f"\n\nПОЗДРАВЛЯЮ! Ты достиг {usr_data[3]} уровня!"
            if usr_data[3] >= 5:
                award_achievement(uid, 4)
            if usr_data[3] >= 10:
                award_achievement(uid, 5)
        await msg.answer(resp, parse_mode="Markdown", reply_markup=main_keyboard())
    except Exception as e:
        await msg.answer(f"Ошибка: {e}", reply_markup=main_keyboard())
# удаление привычки
@router.message(lambda msg: msg.text and msg.text.startswith("Удалить"))
async def del_habit(msg: Message):
    try:
        uid = msg.from_user.id
        usr = get_user(uid)
        if not usr:
            await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
            return
        nums = re.findall(r'\d+', msg.text)
        if not nums:
            await msg.answer("Не удалось определить ID привычки", reply_markup=main_keyboard())
            return
        hid = int(nums[0])
        delete_habit(hid, uid)
        reset_habit_counter()  # сбрасываем счётчик ID после удаления
        await msg.answer("Привычка удалена", reply_markup=main_keyboard())
    except Exception as e:
        await msg.answer(f"Ошибка при удалении: {e}", reply_markup=main_keyboard())
# возврат в главное меню
@router.message(lambda msg: msg.text == "Главное меню")
async def back_to_main_menu(msg: Message):
    await msg.answer("Возвращаюсь в главное меню", reply_markup=main_keyboard())

# начало создания привычки
@router.message(lambda msg: msg.text == "Создать привычку")
async def start_create_habit(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    await state.set_state(HabitForm.name)
    await msg.answer(
        "Шаг 1 из 5: Введи название привычки\n",
        reply_markup=cancel_kb()
    )
# обработка названия
@router.message(HabitForm.name)
async def get_name(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await state.clear()
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    if msg.text == "Отмена":
        await state.clear()
        await msg.answer("Создание привычки отменено", reply_markup=main_keyboard())
        return
    await state.update_data(name=msg.text)
    await state.set_state(HabitForm.description)
    await msg.answer(
        "Шаг 2 из 5: Напиши описание привычки\n",
        reply_markup=back_cancel_kb()
    )
# обработка описания
@router.message(HabitForm.description)
async def get_desc(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    usr = get_user(uid)

    if not usr:
        await state.clear()
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    if msg.text == "Отмена":
        await state.clear()
        await msg.answer("Создание привычки отменено", reply_markup=main_keyboard())
        return
    if msg.text == "Назад":
        await state.set_state(HabitForm.name)
        data = await state.get_data()
        cur_name = data.get('name', '')
        await msg.answer(
            f"Шаг 1 из 5: Введи название привычки\n"
            f"Текущее значение: {cur_name}\n"
            f"Введи новое или оставь как есть",
            reply_markup=cancel_kb()
        )
        return
    await state.update_data(description=msg.text)
    await state.set_state(HabitForm.difficulty)
    await msg.answer(
        "Шаг 3 из 5: Выбери сложность\n"
        "- легко (+10 XP)\n"
        "- средне (+25 XP)\n"
        "- сложно (+50 XP)",
        reply_markup=back_cancel_kb()
    )
# обработка сложности
@router.message(HabitForm.difficulty)
async def get_diff(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await state.clear()
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    if msg.text == "Отмена":
        await state.clear()
        await msg.answer("Создание привычки отменено", reply_markup=main_keyboard())
        return
    if msg.text == "Назад":
        await state.set_state(HabitForm.description)
        data = await state.get_data()
        cur_desc = data.get('description', '')
        await msg.answer(
            f"Шаг 2 из 5: Напиши описание привычки\n"
            f"Текущее значение: {cur_desc}\n"
            f"Введи новое или оставь как есть",
            reply_markup=back_cancel_kb()
        )
        return
    if msg.text not in ['легко', 'средне', 'сложно']:
        await msg.answer(
            "Пожалуйста, выбери из вариантов: легко, средне или сложно",
            reply_markup=back_cancel_kb()
        )
        return
    await state.update_data(difficulty=msg.text)
    await state.set_state(HabitForm.periodicity_unit)
    await msg.answer(
        "Шаг 4 из 5: Выбери единицу измерения периодичности",
        reply_markup=period_inline_kb()
    )
# выбор единицы измерения
@router.callback_query(lambda c: c.data.startswith('unit_'))
async def get_period_unit(callback, state: FSMContext):
    uid = callback.from_user.id
    usr = get_user(uid)
    if not usr:
        await callback.message.edit_text("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        await callback.answer()
        return
    unit_map = {
        'unit_day': 'День',
        'unit_month': 'Месяц',
        'unit_year': 'Год'
    }
    selected_unit = unit_map.get(callback.data, 'День')
    await state.update_data(periodicity_unit=selected_unit)
    await state.set_state(HabitForm.periodicity_value)
    unit_text = {'День': 'дней', 'Месяц': 'месяцев', 'Год': 'лет'}
    unit_name = {'День': 'день', 'Месяц': 'месяц', 'Год': 'год'}
    await callback.message.edit_text(
        f"Шаг 5 из 5: Введи количество {unit_text[selected_unit]}\n"
        f"Если выберешь 1 {unit_name[selected_unit]} — привычка будет доступна раз в {unit_name[selected_unit]}."
    )
    await callback.message.answer(
        "Введи число:",
        reply_markup=back_cancel_kb()
    )
    await callback.answer()
# ввод числа для периодичности
@router.message(HabitForm.periodicity_value)
async def get_period_val(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    usr = get_user(uid)
    if not usr:
        await state.clear()
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    if msg.text == "Отмена":
        await state.clear()
        await msg.answer("Создание привычки отменено", reply_markup=main_keyboard())
        return
    if msg.text == "Назад":
        await state.set_state(HabitForm.periodicity_unit)
        await msg.answer(
            "Шаг 4 из 5: Выбери единицу измерения периодичности",
            reply_markup=period_inline_kb()
        )
        return
    try:
        val = int(msg.text)
        if val <= 0:
            await msg.answer("Введи положительное число (1, 2, 3...)", reply_markup=back_cancel_kb())
            return
    except ValueError:
        await msg.answer("Введи число, например: 1, 2, 3...", reply_markup=back_cancel_kb())
        return
    data = await state.get_data()
    # проверяем, что все данные есть
    if 'name' not in data or 'description' not in data or 'difficulty' not in data or 'periodicity_unit' not in data:
        await state.clear()
        await msg.answer(
            "Произошла ошибка. Данные не сохранились.\n\n"
            "Пожалуйста, начни создание привычки заново: кнопка 'Создать привычку'",
            reply_markup=main_keyboard()
        )
        return
    unit = data.get('periodicity_unit')
    # функция для правильного склонения
    def plural_form(n, form1, form2, form5):
        if 10 <= n % 100 <= 20:
            return form5
        if n % 10 == 1:
            return form1
        if 2 <= n % 10 <= 4:
            return form2
        return form5
    # считаем дни в зависимости от выбранной единицы
    if unit == 'День':
        period_days = val
        period_str = f"{val} {plural_form(val, 'день', 'дня', 'дней')}"
    elif unit == 'Месяц':
        period_days = val * 30
        period_str = f"{val} {plural_form(val, 'месяц', 'месяца', 'месяцев')}"
    else:  # Год
        period_days = val * 365
        period_str = f"{val} {plural_form(val, 'год', 'года', 'лет')}"
    # сохраняем привычку в бд
    add_habit(
        uid,
        data['name'],
        data['description'],
        data['difficulty'],
        period_days,
        period_str
    )
    # выдаём ачивку "Первый шаг"
    award_achievement(uid, 1)
    await state.clear()
    resp = f"Привычка '{data['name']}' создана!\n"
    resp += f"Описание: {data['description']}\n"
    resp += f"Сложность: {data['difficulty']}\n"
    resp += f"Периодичность: {period_str}\n"
    resp += f"Награда: {xp_for_difficulty[data['difficulty']]} XP за выполнение"
    await msg.answer(resp, reply_markup=main_keyboard())
# отмена любого действия
@router.message(lambda msg: msg.text == "Отмена")
async def cancel_action(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Действие отменено", reply_markup=main_keyboard())