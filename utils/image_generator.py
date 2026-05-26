# модуль для генерации карточки персонажа (через Pillow)
# тут подгружаются картинки персонажей в зависимости от класса и уровня
from PIL import Image, ImageDraw, ImageFont
import os
IMG_PATH = "/home/mypc/PycharmProjects/habit_rpg_bot/images/characters"
# загрузка шрифта с поддержкой кириллицы
def get_font(sz):
    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
    ]
    for p in fonts:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except:
                continue
    return ImageFont.load_default()
# получаем картинку персонажа по классу и уровню
def get_char_img(cls, lvl):
    # определяем тир (1,5,10,20)
    if lvl >= 20:
        tier = 20
    elif lvl >= 10:
        tier = 10
    elif lvl >= 5:
        tier = 5
    else:
        tier = 1
    # маппинг класса на имя файла
    if cls == 'Воин' or cls == 19 or cls == '19':
        fname = f"warrior_lvl{tier}.png"
    elif cls == 'Маг' or cls == 18 or cls == '18':
        fname = f"mage_lvl{tier}.png"
    elif cls == 'Разбойник' or cls == 20 or cls == '20':
        fname = f"rogue_lvl{tier}.png"
    else:
        fname = f"warrior_lvl{tier}.png"
    path = os.path.join(IMG_PATH, fname)
    if os.path.exists(path):
        return Image.open(path).convert('RGBA')
    else:
        # заглушка если картинка не найдена
        img = Image.new('RGB', (200, 200), color=(100, 100, 100))
        d = ImageDraw.Draw(img)
        d.text((100, 100), f"{cls}\nLVL{lvl}", fill=(255, 255, 255))
        return img
# главная функция генерации карточки
def gen_card(data):
    w = 600
    h = 800
    # фон
    card = Image.new('RGB', (w, h), color=(20, 15, 35))
    d = ImageDraw.Draw(card)
    # шрифты
    font_title = get_font(28)
    font_txt = get_font(18)
    font_small = get_font(14)
    # данные из словаря
    name = data.get('name', 'Игрок')
    lvl = data.get('level', 1)
    cls = data.get('class', 'Воин')
    skill_pts = data.get('skill_points', 0)
    exp = data.get('exp', 0)
    exp_next = data.get('exp_to_next', 100)
    st = data.get('strength', 1)
    it = data.get('intelligence', 1)
    ag = data.get('agility', 1)
    # имя в верхней части
    d.text((w // 2, 30), name, fill=(218, 165, 32), anchor="mm", font=font_title)
    # рисуем персонажа
    char_img = get_char_img(cls, lvl)
    # уменьшаем для воина и мага 10+ уровня
    if (cls == 'Воин' or cls == 19 or cls == '19') and lvl >= 10:
        char_img = char_img.resize((300, 300), Image.LANCZOS)
    elif (cls == 'Маг' or cls == 18 or cls == '18') and lvl >= 10:
        char_img = char_img.resize((320, 320), Image.LANCZOS)
    cw, ch = char_img.size
    cx = (w - cw) // 2
    cy = 80
    card.paste(char_img, (cx, cy), char_img)
    # класс и уровень под персонажем
    d.text((w // 2, cy + ch + 10), f"{cls} | Уровень {lvl}", fill=(218, 165, 32), anchor="mm", font=font_txt)
    # прогресс бар опыта
    bar_w = 460
    bar_x = (w - bar_w) // 2
    bar_y = cy + ch + 50
    percent = min(1.0, exp / exp_next) if exp_next > 0 else 0
    filled = int(bar_w * percent)
    d.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 22], fill=(40, 35, 60), outline=(100, 80, 120))
    d.rectangle([bar_x, bar_y, bar_x + filled, bar_y + 22], fill=(0, 200, 100))
    d.text((w // 2, bar_y + 35), f"Опыт: {exp} / {exp_next}", fill=(200, 200, 200), anchor="mm", font=font_small)
    # очки навыков
    d.text((w // 2, bar_y + 65), f"Очки навыков: {skill_pts}", fill=(255, 215, 0), anchor="mm", font=font_txt)
    # блок характеристик внизу
    stats_y = h - 180
    d.text((w // 2, stats_y), "ХАРАКТЕРИСТИКИ", fill=(218, 165, 32), anchor="mm", font=font_txt)
    # характеристики с полосками
    stats = [
        ("СИЛА", st, (255, 150, 150)),
        ("ИНТЕЛЛЕКТ", it, (150, 150, 255)),
        ("ЛОВКОСТЬ", ag, (150, 255, 150))
    ]
    start_y = stats_y + 35
    for i, (nm, val, col) in enumerate(stats):
        ypos = start_y + i * 35
        d.text((60, ypos), nm, fill=col, font=font_small)
        d.text((320, ypos), str(val), fill=(255, 215, 0), font=font_small)
        bar_len = min(200, val * 4)
        d.rectangle([360, ypos - 3, 560, ypos + 10], fill=(50, 50, 70), outline=(100, 80, 120))
        d.rectangle([360, ypos - 3, 360 + bar_len, ypos + 10], fill=col)
    return card