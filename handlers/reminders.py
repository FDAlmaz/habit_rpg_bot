# модуль для отправки напоминаний о привычках
# проверяет каждые 30 секунд и отправляет уведомление за половину периода до окончания
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.database import get_conn as get_connection
from create_bot import bot
from datetime import datetime, timedelta
# планировщик задач
scheduler = AsyncIOScheduler()
# словарь для отслеживания уже отправленных напоминаний (чтобы не спамить)
sent_reminders = {}
def setup_reminders():
    # запускаем проверку каждые 30 секунд
    scheduler.add_job(check_and_send_reminders, 'interval', seconds=30)
    scheduler.start()
    print("Система напоминаний запущена")
# форматирует оставшееся время в человекочитаемый вид
def fmt_time(sec):
    if sec < 60:
        return f"{int(sec)} сек."
    elif sec < 3600:
        mins = int(sec // 60)
        secs = int(sec % 60)
        if secs > 0:
            return f"{mins} мин. {secs} сек."
        else:
            return f"{mins} мин."
    elif sec < 86400:
        hrs = int(sec // 3600)
        mins = int((sec % 3600) // 60)
        if mins > 0:
            return f"{hrs} ч. {mins} мин."
        else:
            return f"{hrs} ч."
    else:
        days = int(sec // 86400)
        return f"{days} д."
# основная функция проверки
async def check_and_send_reminders():
    conn = get_connection()
    cur = conn.cursor()
    # получаем все привычки у которых есть last_done
    cur.execute('''
        SELECT id, name, user_id, last_done, period_days
        FROM habits
        WHERE last_done IS NOT NULL
    ''')
    habits = cur.fetchall()
    conn.close()
    now = datetime.now()
    for h in habits:
        hid, name, uid, last_str, period_days = h
        # считаем сколько прошло секунд с последнего выполнения
        last_date = datetime.fromisoformat(last_str)
        elapsed = (now - last_date).total_seconds()
        period_sec = period_days * 24 * 3600
        # если период ещё не закончился
        if elapsed < period_sec:
            remaining = period_sec - elapsed
            half = period_sec // 2  # половина периода
            # отправляем напоминание за половину периода
            if abs(remaining - half) < 15:
                # проверяем не отправляли ли уже это напоминание (кеш на 60 секунд)
                cache_key = f"reminder_{hid}_{half}"
                if cache_key in sent_reminders and (now - sent_reminders[cache_key]).seconds < 60:
                    continue
                sent_reminders[cache_key] = now
                time_str = fmt_time(remaining)
                try:
                    await bot.send_message(
                        uid,
                        f"Напоминание!\n\n"
                        f"Пора выполнить привычку: {name}\n"
                        f"Осталось {time_str}\n\n"
                        f"Выполни её в меню 'Мои привычки'"
                    )
                    print(f"Напоминание для {name} (осталось {time_str})")
                except Exception as e:
                    print(f"Ошибка отправки: {e}")