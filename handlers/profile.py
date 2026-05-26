# модуль для отображения профиля персонажа
# генерирует картинку с персонажем и его характеристиками
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from database.database import get_user, get_stats as get_user_skills
from utils.image_generator import gen_card as generate_profile_card
import io
router = Router()
# обработчик кнопки "Мой профиль" и команды /profile
@router.message(lambda msg: msg.text == "Мой профиль")
@router.message(Command("profile"))
async def show_profile(msg: Message):
    uid = msg.from_user.id
    usr = get_user(uid)  # получаем данные пользователя из бд
    if not usr:
        await msg.answer("Твой аккаунт не найден. Напиши /start, чтобы создать нового персонажа!")
        return
    skills = get_user_skills(uid)  # получаем навыки (сила, интеллект, ловкость)
    # юзернейм или если нет то айди
    uname = usr[1] if usr[1] else f"user_{usr[0]}"
    # собираем данные для генерации картинки
    # usr[3] - уровень, usr[4] - опыт, usr[10] - класс
    # skills[0] - сила, skills[1] - интеллект, skills[2] - ловкость, skills[3] - очки навыков
    user_data = {
        'name': f"@{uname}",
        'level': usr[3],
        'exp': usr[4],
        'exp_to_next': usr[3] * 100,  # нужно 100 опыта на каждый уровень
        'strength': skills[0] if skills else 1,
        'intelligence': skills[1] if skills else 1,
        'agility': skills[2] if skills else 1,
        'skill_points': skills[3] if skills else 0,
        'class': usr[10] if len(usr) > 10 and usr[10] else 'Воин'  # класс или дефолт
    }
    # генерируем картинку через библиотеку Pillow
    img = generate_profile_card(user_data)
    # сохраняем картинку в байты и отправляем
    with io.BytesIO() as out:
        img.save(out, format='PNG')
        out.seek(0)
        photo = BufferedInputFile(out.getvalue(), filename="profile.png")
        await msg.answer_photo(photo=photo, caption=f"Профиль {user_data['name']}")