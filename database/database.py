# модуль для работы с базой данных sqlite3
# тут все функции для работы с пользователями, привычками, ачивками, pvp и тд
from datetime import datetime, timedelta
import sqlite3
DB_PATH = "habit_bot.db"
# подключение к бд
def get_conn():
    return sqlite3.connect(DB_PATH)
# создание всех таблиц и начальных данных
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # таблица пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            skill_pts INTEGER DEFAULT 0,
            str_stat INTEGER DEFAULT 1,
            int_stat INTEGER DEFAULT 1,
            agi_stat INTEGER DEFAULT 1,
            end_stat INTEGER DEFAULT 1,
            class_type TEXT DEFAULT 'Новичок',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # таблица друзей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            user_id INTEGER,
            friend_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, friend_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (friend_id) REFERENCES users(user_id)
        )
    ''')
    # таблица привычек
    cur.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            descr TEXT,
            diff TEXT,
            period_days INTEGER DEFAULT 1,
            period_str TEXT DEFAULT 'ежедневно',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_done TIMESTAMP,
            cur_streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    # логи выполнения привычек
    cur.execute('''
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER,
            user_id INTEGER,
            done_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            xp_gained INTEGER,
            bonus_xp INTEGER DEFAULT 0,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        )
    ''')
    # таблица ачивок
    cur.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            descr TEXT,
            cond_type TEXT,
            cond_val INTEGER
        )
    ''')
    # полученные ачивки
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            user_id INTEGER,
            ach_id INTEGER,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, ach_id)
        )
    ''')
    # pvp битвы
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pvp_battles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ch_id INTEGER,
            opp_id INTEGER,
            ch_power INTEGER,
            opp_power INTEGER,
            winner_id INTEGER,
            battle_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ch_id) REFERENCES users(user_id),
            FOREIGN KEY (opp_id) REFERENCES users(user_id)
        )
    ''')
    # кулдаун pvp
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pvp_cooldown (
            user_id INTEGER,
            opp_id INTEGER,
            last_time TIMESTAMP,
            PRIMARY KEY (user_id, opp_id)
        )
    ''')
    # добавляем стандартные ачивки
    cur.execute('''
        INSERT OR IGNORE INTO achievements (id, name, descr, cond_type, cond_val)
        VALUES
            (1, 'Первый шаг', 'Создать первую привычку', 'create_habit', 1),
            (2, 'Старатель', 'Выполнить 10 привычек', 'complete_habit', 10),
            (3, 'Марафонец', 'Выполнять привычки 7 дней подряд', 'streak_7', 7),
            (4, 'Мастер', 'Достичь 5 уровня', 'level', 5),
            (5, 'Легенда', 'Достичь 10 уровня', 'level', 10),
            (6, 'Сила духа', 'Выполнить 20 сложных привычек', 'hard_habits', 20),
            (7, 'Творец', 'Создать 10 привычек', 'create_habit', 10),
            (8, 'Первый победитель', 'Одержать первую победу в PvP', 'pvp_win', 1)
    ''')
    conn.commit()
    conn.close()
    print("База данных инициализирована")
# регистрация нового пользователя
def reg_user(uid, uname, fname):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', (uid, uname, fname))
    conn.commit()
    conn.close()
# получить данные пользователя
def get_user(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_id = ?', (uid,))
    u = cur.fetchone()
    conn.close()
    return u
# обновить класс персонажа
def upd_class(uid, cls):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE users SET class_type = ? WHERE user_id = ?', (cls, uid))
    conn.commit()
    conn.close()
# начисление опыта (с бонусом за серию)
def add_exp(uid, xp_gain, bonus=0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT exp, level FROM users WHERE user_id = ?', (uid,))
    exp, lvl = cur.fetchone()
    total = xp_gain + bonus
    new_exp = exp + total
    new_lvl = lvl
    ups = 0
    # формула: 100 опыта на уровень
    while new_exp >= new_lvl * 100:
        new_exp -= new_lvl * 100
        new_lvl += 1
        ups += 1
    cur.execute('UPDATE users SET exp = ?, level = ?, skill_pts = skill_pts + ? WHERE user_id = ?', (new_exp, new_lvl, ups, uid))
    conn.commit()
    conn.close()
    return new_lvl > lvl
# создание привычки
def add_habit(uid, name, desc, diff, period_days, period_str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO habits (user_id, name, descr, diff, period_days, period_str, cur_streak, best_streak)
        VALUES (?, ?, ?, ?, ?, ?, 0, 0)
    ''', (uid, name, desc, diff, period_days, period_str))
    conn.commit()
    conn.close()
# получить все привычки пользователя
def get_habits(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, name, descr, diff, period_str, cur_streak, best_streak FROM habits WHERE user_id = ?', (uid,))
    res = cur.fetchall()
    conn.close()
    return res
# удалить привычку
def del_habit(hid, uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM habits WHERE id = ? AND user_id = ?', (hid, uid))
    conn.commit()
    conn.close()
# логирование выполнения привычки
def log_habit_done(hid, uid, xp_gain):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT last_done, cur_streak, period_days, best_streak FROM habits WHERE id = ? AND user_id = ?', (hid, uid))
    h = cur.fetchone()
    if not h:
        conn.close()
        return 0, 0
    last_str, cur_streak, period_days, best = h
    now = datetime.now()
    # проверяем просрочку
    if last_str:
        last_date = datetime.fromisoformat(last_str)
        next_avail = last_date + timedelta(days=period_days)
        if now > next_avail:
            cur_streak = 0
    new_streak = cur_streak + 1
    if new_streak > best:
        best = new_streak
    cur.execute('UPDATE habits SET last_done = ?, cur_streak = ?, best_streak = ? WHERE id = ?', (now.isoformat(), new_streak, best, hid))
    bonus = new_streak
    cur.execute('INSERT INTO habit_logs (habit_id, user_id, xp_gained, bonus_xp) VALUES (?, ?, ?, ?)', (hid, uid, xp_gain, bonus))
    conn.commit()
    conn.close()
    return new_streak, bonus
# топ-10 пользователей
def get_top(limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT first_name, level, exp FROM users ORDER BY level DESC, exp DESC LIMIT ?', (limit,))
    res = cur.fetchall()
    conn.close()
    return res
# ачивки пользователя
def get_user_achs(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT a.name, a.descr FROM user_achievements ua JOIN achievements a ON ua.ach_id = a.id WHERE ua.user_id = ?', (uid,))
    res = cur.fetchall()
    conn.close()
    return res
# выдать ачивку
def give_ach(uid, aid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO user_achievements (user_id, ach_id) VALUES (?, ?)', (uid, aid))
    conn.commit()
    conn.close()
# отправить заявку в друзья
def send_friend_req(uid, friend_uname, req_name=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users WHERE username = ?', (friend_uname,))
    friend = cur.fetchone()
    if not friend:
        conn.close()
        return False, "Пользователь не найден"
    fid = friend[0]
    if uid == fid:
        conn.close()
        return False, "Нельзя добавить себя"
    cur.execute('SELECT * FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)', (uid, fid, fid, uid))
    if cur.fetchone():
        conn.close()
        return False, "Заявка уже существует или вы уже друзья"
    cur.execute('INSERT INTO friends (user_id, friend_id, status) VALUES (?, ?, "pending")', (uid, fid))
    conn.commit()
    conn.close()
    return True, f"Заявка отправлена пользователю {friend_uname}"
# принять заявку
def accept_friend(uid, friend_uname):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users WHERE username = ?', (friend_uname,))
    friend = cur.fetchone()
    if not friend:
        conn.close()
        return False, "Пользователь не найден"
    fid = friend[0]
    cur.execute('UPDATE friends SET status = "accepted" WHERE user_id = ? AND friend_id = ? AND status = "pending"', (fid, uid))
    if cur.rowcount == 0:
        conn.close()
        return False, "Нет заявки от этого пользователя"
    conn.commit()
    conn.close()
    return True, f"Теперь вы друзья с {friend_uname}"
# список друзей
def get_friends_list(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT u.user_id, u.username, u.first_name, u.level, u.exp
        FROM friends f
        JOIN users u ON (f.friend_id = u.user_id OR f.user_id = u.user_id)
        WHERE (f.user_id = ? OR f.friend_id = ?) AND f.status = "accepted" AND u.user_id != ?
    ''', (uid, uid, uid))
    res = cur.fetchall()
    conn.close()
    return res


# рейтинг среди друзей
def get_friends_rank(uid):
    conn = get_conn()
    cur = conn.cursor()

    # Получаем ID друзей пользователя
    cur.execute('''
        SELECT friend_id FROM friends 
        WHERE user_id = ? AND status = 'accepted'
        UNION
        SELECT user_id FROM friends 
        WHERE friend_id = ? AND status = 'accepted'
    ''', (uid, uid))

    friends = cur.fetchall()
    friend_ids = [row[0] for row in friends]

    # Добавляем самого пользователя
    friend_ids.append(uid)

    if not friend_ids:
        res = []
    else:
        placeholders = ','.join(['?'] * len(friend_ids))
        cur.execute(f'''
            SELECT u.user_id, u.username, u.first_name, u.level, u.exp
            FROM users u
            WHERE u.user_id IN ({placeholders})
            ORDER BY u.level DESC, u.exp DESC
        ''', friend_ids)
        res = cur.fetchall()

    conn.close()
    return res
# входящие заявки
def get_pending(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT u.username, u.first_name FROM friends f JOIN users u ON f.user_id = u.user_id WHERE f.friend_id = ? AND f.status = "pending"', (uid,))
    res = cur.fetchall()
    conn.close()
    return res
# добавить очки навыков
def add_skill_pts(uid, pts):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE users SET skill_pts = skill_pts + ? WHERE user_id = ?', (pts, uid))
    conn.commit()
    conn.close()
# улучшить навык
def upgrade_stat(uid, stat_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT skill_pts FROM users WHERE user_id = ?', (uid,))
    res = cur.fetchone()
    if not res:
        conn.close()
        return False, "Пользователь не найден"
    pts = res[0]
    if pts <= 0:
        conn.close()
        return False, "Нет очков навыков!"
    if stat_name == 'сила':
        cur.execute('UPDATE users SET str_stat = str_stat + 1, skill_pts = skill_pts - 1 WHERE user_id = ?', (uid,))
    elif stat_name == 'интеллект':
        cur.execute('UPDATE users SET int_stat = int_stat + 1, skill_pts = skill_pts - 1 WHERE user_id = ?', (uid,))
    elif stat_name == 'ловкость':
        cur.execute('UPDATE users SET agi_stat = agi_stat + 1, skill_pts = skill_pts - 1 WHERE user_id = ?', (uid,))
    else:
        conn.close()
        return False, "Неизвестный навык"
    conn.commit()
    cur.execute('SELECT str_stat, int_stat, agi_stat, skill_pts FROM users WHERE user_id = ?', (uid,))
    stats = cur.fetchone()
    conn.close()
    return True, f"Навык улучшен! Осталось очков: {stats[3]}"
# получить навыки пользователя
def get_stats(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT str_stat, int_stat, agi_stat, skill_pts FROM users WHERE user_id = ?', (uid,))
    s = cur.fetchone()
    conn.close()
    return s if s else (1, 1, 1, 0)
# все ачивки с прогрессом
def get_all_achs_with_progress(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, name, descr, cond_type, cond_val FROM achievements')
    achs = cur.fetchall()
    cur.execute('SELECT ach_id FROM user_achievements WHERE user_id = ?', (uid,))
    earned = [row[0] for row in cur.fetchall()]
    # собираем прогресс
    cur.execute('SELECT COUNT(*) FROM habits WHERE user_id = ?', (uid,))
    habits_cnt = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM habit_logs WHERE user_id = ?', (uid,))
    compl_cnt = cur.fetchone()[0]
    cur.execute('SELECT level FROM users WHERE user_id = ?', (uid,))
    lvl = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM habit_logs hl JOIN habits h ON hl.habit_id = h.id WHERE hl.user_id = ? AND h.diff = "сложно"', (uid,))
    hard_cnt = cur.fetchone()[0]
    cur.execute('SELECT MAX(cur_streak) FROM habits WHERE user_id = ?', (uid,))
    max_str = cur.fetchone()[0] or 0
    conn.close()
    prog = {'habits_cnt': habits_cnt, 'compl_cnt': compl_cnt, 'lvl': lvl, 'hard_cnt': hard_cnt, 'streak': max_str}
    res = []
    for a in achs:
        aid, name, desc, ctype, cval = a
        is_earned = aid in earned
        cur_val = 0
        if ctype == 'create_habit':
            cur_val = prog['habits_cnt']
        elif ctype == 'complete_habit':
            cur_val = prog['compl_cnt']
        elif ctype == 'streak_7':
            cur_val = prog['streak']
        elif ctype == 'level':
            cur_val = prog['lvl']
        elif ctype == 'hard_habits':
            cur_val = prog['hard_cnt']
        res.append({'id': aid, 'name': name, 'descr': desc, 'current': cur_val, 'required': cval, 'earned': is_earned})
    return res
# форматирование времени ожидания
def fmt_wait(sec):
    if sec < 60:
        return f"Скоро (через {sec} сек.)"
    elif sec < 3600:
        mins = sec // 60
        secs = sec % 60
        if secs > 0:
            return f"Скоро (через {mins} мин. {secs} сек.)"
        else:
            return f"Скоро (через {mins} мин.)"
    elif sec < 86400:
        hrs = sec // 3600
        mins = (sec % 3600) // 60
        if mins > 0:
            return f"Скоро (через {hrs} ч. {mins} мин.)"
        else:
            return f"Скоро (через {hrs} ч.)"
    else:
        days = sec // 86400
        return f"Скоро (через {days} д.)"
# проверка можно ли выполнить привычку
def can_do_habit(hid, uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT last_done, period_days FROM habits WHERE id = ? AND user_id = ?', (hid, uid))
    h = cur.fetchone()
    if not h:
        conn.close()
        return "Привычка не найдена", False, 1
    last_str, period_days = h
    if not last_str:
        conn.close()
        return "", True, period_days
    last_date = datetime.fromisoformat(last_str)
    next_avail = last_date + timedelta(days=period_days)
    now = datetime.now()
    if now >= next_avail:
        conn.close()
        return "", True, period_days
    remaining = (next_avail - now).total_seconds()
    conn.close()
    return fmt_wait(int(remaining)), False, period_days
# расчёт силы для pvp (с учётом класса)
def get_pvp_power(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT level, str_stat, int_stat, agi_stat, class_type FROM users WHERE user_id = ?', (uid,))
    u = cur.fetchone()
    conn.close()
    if not u:
        return 0, ""
    lvl, st, it, ag, cls = u
    power = (st * 2) + (it * 1.5) + (ag * 1.5) + (lvl * 5)
    bonus = ""
    if cls == 'Воин':
        power = (st * 2 * 1.3) + (it * 1.5) + (ag * 1.5) + (lvl * 5)
        bonus = "Ярость Воина +30%"
    elif cls == 'Маг':
        power = (st * 2) + (it * 1.5 * 1.3) + (ag * 1.5) + (lvl * 5)
        bonus = "Мудрость Мага +30%"
    elif cls == 'Разбойник':
        power = (st * 2) + (it * 1.5) + (ag * 1.5 * 1.3) + (lvl * 5)
        bonus = "Скрытность Разбойника +30%"
    return int(power), bonus
# проверка pvp кулдауна
def can_pvp(uid, opp_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT last_time FROM pvp_cooldown WHERE user_id = ? AND opp_id = ?', (uid, opp_id))
    res = cur.fetchone()
    conn.close()
    if not res:
        return True, ""
    last = datetime.fromisoformat(res[0])
    if datetime.now() - last < timedelta(days=1):
        hours_left = 24 - (datetime.now() - last).seconds // 3600
        return False, f"Ты уже вызывал этого игрока сегодня. Осталось {hours_left} ч."
    return True, ""
# сохранить кулдаун pvp
def save_pvp_cd(uid, opp_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO pvp_cooldown (user_id, opp_id, last_time) VALUES (?, ?, ?)', (uid, opp_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
# сохранить результат битвы
def save_pvp_battle(ch_id, opp_id, ch_pow, opp_pow, win_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO pvp_battles (ch_id, opp_id, ch_power, opp_power, winner_id) VALUES (?, ?, ?, ?, ?)', (ch_id, opp_id, ch_pow, opp_pow, win_id))
    conn.commit()
    conn.close()
# полное удаление аккаунта
def del_account(uid):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM habits WHERE user_id = ?', (uid,))
        cur.execute('DELETE FROM habit_logs WHERE user_id = ?', (uid,))
        cur.execute('DELETE FROM friends WHERE user_id = ? OR friend_id = ?', (uid, uid))
        cur.execute('DELETE FROM user_achievements WHERE user_id = ?', (uid,))
        cur.execute('DELETE FROM pvp_battles WHERE ch_id = ? OR opp_id = ?', (uid, uid))
        cur.execute('DELETE FROM pvp_cooldown WHERE user_id = ? OR opp_id = ?', (uid, uid))
        cur.execute('DELETE FROM users WHERE user_id = ?', (uid,))
        conn.commit()
        conn.close()
        return True, "Аккаунт удалён"
    except Exception as e:
        conn.close()
        return False, str(e)
# сбросить счётчик ID привычек (чтобы новые ID начинались с 1)
def reset_habit_counter():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM habits")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='habits'")
    conn.commit()
    conn.close()