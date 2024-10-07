import sqlite3
import logging
from datetime import datetime, timedelta
import pytz

# Часовой пояс Москва
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

def get_current_moscow_time():
    return datetime.now(MOSCOW_TZ)

# Подключение к базе данных
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()

# Создание таблицы пользователей, если она еще не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT
                )''')
conn.commit()

# Функция для добавления нового пользователя с правильным chat_id
def add_user(user_id, username, first_name, last_name, chat_id):
    cursor.execute('INSERT INTO users (id, username, first_name, last_name, chat_id) VALUES (?, ?, ?, ?, ?)',
                   (user_id, username, first_name, last_name, chat_id))
    conn.commit()

# Функция для добавления нового пользователя с правильны
def add_user_start(user_id, username, first_name, last_name):
    cursor.execute('INSERT INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                   (user_id, username, first_name, last_name))
    conn.commit()    

# Функция для проверки, есть ли пользователь уже в базе данных
def user_exists(user_id):
    cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
    return cursor.fetchone() is not None

# Функция для получения количества рефералов пользователя из базы данных
def get_user_referrals(user_id):
    cursor.execute('SELECT refs FROM users WHERE id=?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return 0  # Возвращаем 0, если пользователь не найден

# Функция для увеличения количества рефералов пользователя
def increment_user_referrals(user_id):
    cursor.execute('UPDATE users SET refs = refs + 1 WHERE id=?', (user_id,))
    conn.commit()

# Функция для получения списка всех пользователей из базы данных
def get_all_users():
    cursor.execute('SELECT * FROM users')
    return cursor.fetchall()

# Функция для получения количества пользователей в базе данных
def get_num_users():
    cursor.execute('SELECT COUNT(*) FROM users')
    return cursor.fetchone()[0]

# Функция для получения пользователя по ID
def get_user(user_id):
    logging.info(f"Запрос пользователя с ID: {user_id}")
    cursor.execute('SELECT id, username, first_name, last_name, chat_id, status FROM users WHERE id=?', (user_id,))
    return cursor.fetchone()

def chat_exists(chat_id):
    # Код для проверки, существует ли chat_id в таблице chats
    query = "SELECT COUNT(*) FROM chats WHERE chat_id = ?"
    cursor.execute(query, (chat_id,))
    result = cursor.fetchone()
    return result[0] > 0  # Возвращает True, если chat_id существует

def add_chat(chat_id, chat_name):
    # Код для добавления chat_id и chat_name в таблицу chats
    query = "INSERT INTO chats (chat_id, chat_name) VALUES (?, ?)"
    cursor.execute(query, (chat_id, chat_name))
    conn.commit()  # Не забудьте сохранить изменения в базе данных

def get_chat_name(chat_id):
    # Код для получения названия чата по chat_id
    query = "SELECT chat_name FROM chats WHERE chat_id = ?"
    cursor.execute(query, (chat_id,))
    result = cursor.fetchone()
    return result[0] if result else None  # Возвращаем имя чата или None, если не найдено

# Добавьте эту функцию в ваш модуль database
def get_all_chat_ids():
    query = "SELECT chat_id FROM chats"  # SQL-запрос для получения всех chat_id
    cursor.execute(query)
    return cursor.fetchall()  # Возвращает список всех chat_id

# Функция для получения chat_id текущего пользователя из базы данных
def get_user_chat_ids(user_id):
    cursor.execute('SELECT chat_id FROM users WHERE id=?', (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        return result[0].split(', ')  # Возвращаем список chat_id, разбитый по запятой
    return []  # Возвращаем пустой список, если нет данных

def update_user_chat_ids(user_id, new_chat_ids):
    # Преобразуем список chat_id в строку с разделением запятыми
    chat_ids_string = ', '.join(new_chat_ids)
    cursor.execute('UPDATE users SET chat_id=? WHERE id=?', (chat_ids_string, user_id))
    conn.commit()  # Не забудьте сохранить изменения в базе данных

# Функция для получения пользователей по chat_id
def get_users_by_chat_id(chat_id):
    cursor.execute('SELECT username, first_name, last_name FROM users WHERE chat_id LIKE ?', ('%'+chat_id+'%',))
    return cursor.fetchall()  # Возвращает список пользователей с заданным chat_id

def get_users_for_spisok(chat_id):
    # Используем LIKE для поиска chat_id в списке
    query = "SELECT first_name, last_name, reserve, reserve_time FROM users WHERE chat_id LIKE ?"
    cursor.execute(query, (f"%{chat_id}%",))  # Добавляем символы % для поиска подстроки
    return cursor.fetchall()  # Возвращает список пользователей с заданным chat_id


# Функция для получения пользователей по chat_id
def get_users_by_chat_id_tegg(chat_id):
    # Преобразуем chat_id в строку
    chat_id_str = str(chat_id)
    cursor.execute('SELECT username, first_name, last_name FROM users WHERE chat_id LIKE ?', ('%' + chat_id_str + '%',))
    return cursor.fetchall()  # Возвращает список пользователей с заданным chat_id

# Функция для обновления статуса пользователя
def update_user_status(user_id, new_status):
    """
    Обновляет статус пользователя в базе данных.
    
    :param user_id: ID пользователя
    :param new_status: Новый статус для пользователя
    """
    query = "UPDATE users SET status = ? WHERE id = ?"
    cursor.execute(query, (new_status, user_id))
    conn.commit()

# Функция для получения пользователя по username
def get_user_by_username(username):
    """
    Возвращает данные пользователя по его username.
    
    :param username: Username пользователя
    :return: Данные пользователя (id, username, first_name, last_name, chat_id, status) или None, если не найден
    """
    query = "SELECT id, username, first_name, last_name, chat_id, status FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    return cursor.fetchone()  # Возвращает первого совпадающего пользователя


def user_exists(user_id):
    cursor.execute('SELECT 1 FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone() is not None  # Возвращает True, если пользователь найден

def get_user_data(user_id):
    # SQL-запрос для получения данных пользователя
    query = "SELECT username, first_name, last_name FROM users WHERE id = ?"
    
    # Выполнение запроса
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    
    # Если пользователь найден, возвращаем данные в виде словаря
    if result:
        return {
            'username': result[0],
            'first_name': result[1],
            'last_name': result[2]
        }
    else:
        # Если пользователь не найден, возвращаем None
        return None

def update_user(user_id, username, first_name, last_name):
    # Запрос для обновления данных пользователя
    query = """
    UPDATE users 
    SET username = ?, first_name = ?, last_name = ?
    WHERE id = ?
    """
    cursor.execute(query, (username, first_name, last_name, user_id))
    conn.commit()

def get_user_by_username(username):
    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    return cursor.fetchone()  # Возвращает первого совпадающего пользователя


# Функция для сброса значения reserve
def reset_user_reserve(user_id):
    query = """
    UPDATE users
    SET reserve = '', reserve_time = NULL
    WHERE id = ?;
    """
    cursor.execute(query, (user_id,))
    conn.commit()

    logging.info(f"Значение для пользователя {user_id} сброшено.")

# Функция для проверки и сброса значения
def check_and_reset_reserve(user_id):
    # Получаем текущее московское время
    current_time = get_current_moscow_time()

    # Получаем последнее сохраненное время резервирования
    cursor.execute('SELECT reserve_time FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()

    if result and result[0]:
        # Преобразуем строку времени в объект datetime с учетом часового пояса
        reserve_time = datetime.strptime(result[0], '%d.%m.%y %H:%M')
        reserve_time = MOSCOW_TZ.localize(reserve_time)  # Делает reserve_time timezone-aware

        # Проверяем, прошло ли более 6ч
        if current_time - reserve_time >= timedelta(hours=6):
            # Сбрасываем резервное значение
            cursor.execute('''
                UPDATE users SET reserve = NULL, reserve_time = ?
                WHERE id = ?
            ''', (current_time.strftime('%d.%m.%y %H:%M'), user_id))
            conn.commit()
            return True

    return False

def reset_user_reserve(user_id):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reserve = NULL WHERE id = ?", (user_id,))
    conn.commit()

def reset_all_user_reserves():
    cursor = conn.cursor()

    # SQL-запрос для сброса значений reserve
    cursor.execute("UPDATE users SET reserve = NULL")  # Предполагая, что столбец reserve называется именно так
    conn.commit()

# Функция обновления времени в базе данных
def update_user_reserve(user_id, reserve):
    current_time = get_current_moscow_time()
    
    # Форматирование времени в виде "DD.MM.YY HH:MM"
    formatted_time = current_time.strftime('%d.%m.%y %H:%M')
    
    # Обновляем значение и время в базе данных
    cursor.execute('''
        UPDATE users SET reserve = ?, reserve_time = ?
        WHERE id = ?
    ''', (reserve, formatted_time, user_id))
    conn.commit()

def get_users_by_chat_id_with_empty_reserve(chat_id):
    query = "SELECT id, username, reserve FROM users WHERE chat_id LIKE ?"
    cursor = conn.cursor()
    cursor.execute(query, (f"%{chat_id}%",))
    
    # Получаем всех пользователей с чат-айди
    users = cursor.fetchall()

    # Отфильтровываем пользователей, у которых reserve пустой или содержит '0', '00', '000'
    filtered_users = [
        user for user in users
        if not user[2] or user[2] in ('0', '00', '000')  # Проверка на пустое значение или 0, 00, 000
    ]

    return filtered_users



# Закрытие соединения с базой данных
def close_connection():
    cursor.close()
    conn.close()
