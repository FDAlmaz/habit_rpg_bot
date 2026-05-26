import asyncio
from create_bot import bot, dp
from handlers import start, profile, habits, rating, achievements, friends, skills, pvp, settings
from database import init_db
from handlers.reminders import setup_reminders
async def main():
    # Подключаем все роутеры
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(habits.router)
    dp.include_router(rating.router)
    dp.include_router(achievements.router)
    dp.include_router(friends.router)
    dp.include_router(skills.router)
    dp.include_router(pvp.router)
    dp.include_router(settings.router)
    # Инициализируем базу данных
    init_db()
    setup_reminders()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())