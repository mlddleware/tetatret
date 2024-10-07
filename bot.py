import logging
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberStatus, ChatMember, ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from datetime import datetime, timedelta
import pytz  # Добавляем для работы с часовыми поясами
import asyncio
import re

from config import API_TOKEN
import database as db

from adminpanel import admin_panel, process_users_button

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ID чата для логирования
LOG_CHAT_ID = -4513223003

# Функция для отправки логов в чат
async def log_to_chat(message: str):
    try:
        await bot.send_message(LOG_CHAT_ID, message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка при отправке логов в чат: {e}")


# Хранение состояния для таймера
reset_task = None

# Функция для проверки, является ли пользователь администратором в БД
async def is_user_admin_in_db(user_id):
    user_data = db.get_user(user_id)
    logging.info(f"Полученные данные о пользователе: {user_data}")
    if user_data:
        return user_data[5] in ['vip', 'admin']  # Проверка на VIP или админа в БД
    return False

# Функция для проверки, является ли пользователь администратором или VIP в БД
async def is_admin_or_owner(chat_id, user_id):
    try:
        # Удаляем проверку статуса участника чата
        return await is_user_admin_in_db(user_id)
    except Exception as e:
        logging.error(f"Ошибка при проверке статуса участника: {e}")
        return False

# Обработка команды /admin
@dp.message_handler(commands=['admin'])
async def handle_admin_panel(message: types.Message):
    if await is_user_admin(message.from_user.id):
        await admin_panel(message)
    else:
        await message.reply("У вас нет доступа к этой команде.")

# Обработка колбэков
@dp.callback_query_handler(lambda query: query.data == 'users')
async def handle_users_callback(callback_query: types.CallbackQuery):
    if await is_user_admin(callback_query.from_user.id):
        await process_users_button(callback_query)
    else:
        await callback_query.answer("У вас нет доступа к этой команде.")

@dp.message_handler(commands=['tegg'])
async def handle_tegg(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    log_text = f"Команда /tegg вызвана пользователем {message.from_user.username} (ID: {user_id}) в чате {chat_id}"
    logging.info(log_text)
    await log_to_chat(log_text)

    # Проверка на администраторские права
    if not await is_admin_or_owner(chat_id, user_id):
        await log_to_chat(f"Пользователю {message.from_user.username} отказано в доступе к команде /tegg")
        return

    text_after_command = message.get_args()
    users = db.get_users_by_chat_id_tegg(chat_id)

    if not users:
        await message.reply("Нет пользователей с данным chat_id для тегания.")
        await log_to_chat(f"Нет пользователей для тегания в чате {chat_id}")
        return

    for user in users:
        username = user[0]
        first_name = user[1]
        last_name = user[2]
        display_name = f"@{username}" if username else f"{first_name} {last_name}".strip()

        tag_message = f"{display_name} {text_after_command}" if text_after_command else display_name

        try:
            await message.reply(tag_message)
            await log_to_chat(f"Тегнул пользователя: {tag_message}")
        except Exception as e:
            error_text = f"Ошибка при тегании пользователя {display_name}: {e}"
            logging.error(error_text)
            await log_to_chat(error_text)


# Обработчик команды /help_comand
@dp.message_handler(Command('help_comand'))
async def send_help(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    log_text = f"Команда /help_comand вызвана пользователем {message.from_user.username} (ID: {user_id})"
    logging.info(log_text)
    await log_to_chat(log_text)

    if not await is_admin_or_owner(chat_id, user_id):
        await log_to_chat(f"Пользователю {message.from_user.username} отказано в доступе к команде /help_comand")
        return

    if message.chat.type == 'private':
        help_text = (
            "/tegg - тегает всех.\n"
            "/fi_tegg - бот пришлет вам теги людей в вашем чате\n"
            "/teg_lvc - бот тегнет всех в личку.\n"
            "/reserv_ba - бот покажет список тех кто отметился, когда они последний раз отметились, сколько тачек стоит, список сбрасывается  24 часа.  \n"
            "/reserve (цифры от 1 до 6, до трёх цифр) - добавляет в список. \n"
            "/teg_reserve_hat - тегает тех у кого не стоит ни одной цифры в списке. \n"
            "/teg_reserve_li - тегает тех у кого не стоит ни одной цифры в списке в личку. \n"
            "/reserv_000r - бот обнуляет список.  \n"
            "/teg_reserve_li - тегает тех у кого не стоит ни одной цифры в списке в личку. \n"
            "/xil1 /xil2 /xil3 (время 1h 20m 30s) бот тегнет вас в чате с сообщением 'тачка отхилилась'\n"
        )
        await message.answer(help_text)
        await log_to_chat(f"Отправлена помощь пользователю {message.from_user.username}")
    else:
        await message.answer("Команда /help доступна только в личных сообщениях.")
        await log_to_chat(f"Пользователь {message.from_user.username} вызвал команду /help не в личных сообщениях")

# Обработка команды /teg_lvc
@dp.message_handler(commands=['teg_lvc'])
async def handle_tag_all_users(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    log_text = f"Команда /teg_lvc вызвана пользователем {message.from_user.username} (ID: {user_id})"
    logging.info(log_text)
    await log_to_chat(log_text)

    if not await is_admin_or_owner(chat_id, user_id):
        await log_to_chat(f"Пользователю {message.from_user.username} отказано в доступе к команде /teg_lvc")
        return

    command_parts = message.text.split(maxsplit=1)
    custom_text = command_parts[1] if len(command_parts) > 1 else ""

    users = db.get_all_users()

    if not users:
        await message.reply("Нет пользователей для тега.")
        await log_to_chat("Нет пользователей для тега.")
        return

    await log_to_chat(f"Начало тегания пользователей администратором {message.from_user.username}")
    for user in users:
        try:
            user_id = user[0]
            username = user[1]
            tag_message = f"@{username} {custom_text}" if username else f"{user[2]} {custom_text}"

            await bot.send_message(user_id, tag_message)
            await log_to_chat(f"Отправлено сообщение пользователю: {username if username else user[2]}")
        except Exception as e:
            error_text = f"Ошибка при отправке сообщения пользователю {user_id}: {e}"
            logging.error(error_text)
            await log_to_chat(error_text)

# Обработка команды /start
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    chat_id = message.chat.id

    log_text = f"Команда /start вызвана пользователем {username} (ID: {user_id})"
    logging.info(log_text)
    await log_to_chat(log_text)

    if not db.user_exists(user_id):
        db.add_user_start(user_id, username, first_name, last_name)
        await log_to_chat(f"Пользователь {username} (ID: {user_id}) добавлен в базу данных")

# Обработка команды /fi_tegg
@dp.message_handler(commands=['fi_tegg'])
async def handle_check_chat_id(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admin_or_owner(chat_id, user_id):
        return

    command_parts = message.text.split(maxsplit=2)

    if len(command_parts) < 2:
        await message.reply("Пожалуйста, укажите chat_id.")
        return

    chat_id = command_parts[1]  # chat_id

    # Если указан текст, берем его, иначе оставляем пустым
    custom_text = command_parts[2] if len(command_parts) > 2 else ""

    if not db.chat_exists(chat_id):
        available_chats = db.get_all_chat_ids()
        available_chat_names = [db.get_chat_name(chat[0]) for chat in available_chats]  # Получаем названия чатов

        # Создаем список chat_id и chat_name в виде отдельных строк
        available_chats_list = "\n".join(f"<code>{chat[0]}</code> - {available_chat_names[i]}" for i, chat in enumerate(available_chats))

        await message.reply(
            f"CHAT_ID = {chat_id}, не найден.\nВот доступные:\n{available_chats_list}",
            parse_mode='HTML'
        )
    else:
        users = db.get_users_by_chat_id(chat_id)

        if users:
            for user in users:
                username = user[0]  # username
                first_name = user[1]  # First_name
                last_name = user[2]  # Last_name

                # Если first_name или last_name = None, они не будут отображаться
                name_parts = [f"@{username}"]  # Обязательно будет username
                if first_name:
                    name_parts.append(first_name)
                if last_name:
                    name_parts.append(last_name)

                # Собираем итоговое имя
                display_name = " ".join(name_parts)

                # Создаем inline-кнопку "Тегнуть"
                keyboard = InlineKeyboardMarkup()
                tag_button = InlineKeyboardButton(
                    text="🗣 Тегнуть",
                    callback_data=f"tag_user:{chat_id}:{username}:{custom_text}"
                )
                keyboard.add(tag_button)

                await message.reply(
                    display_name,  # Отображаем @username с именем и фамилией (если они есть)
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        else:
            await message.reply(f"CHAT_ID = {chat_id}, найден в базе данных, но пользователи не найдены.", parse_mode='HTML')

    # Логируем команду
    await log_to_chat(f"Команда /fi_tegg выполнена пользователем {user_id}. Запрошенный chat_id: {chat_id}.")

# Обработка нажатия на кнопку "Тегнуть"
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('tag_user'))
async def process_callback(callback_query: types.CallbackQuery):
    _, chat_id, username, custom_text = callback_query.data.split(':')

    # Формируем упоминание пользователя
    display_name = f"@{username}"

    try:
        # Тегаем пользователя в указанном чате с дополнительным текстом
        await bot.send_message(chat_id, f"{display_name} {custom_text}")
        await callback_query.answer(f"Пользователь {display_name} успешно отмечен в чате {chat_id}.")
        
        # Логируем тегание пользователя
        await log_to_chat(f"Пользователь {display_name} отмечен в чате {chat_id}.")
    except Exception as e:
        await callback_query.answer(f"Ошибка при попытке тегнуть пользователя: {e}")
        logging.error(f"Ошибка при попытке тегнуть {display_name} в чате {chat_id}: {e}")

# Обработка команды /teg_reserve_hat
@dp.message_handler(commands=['teg_reserve_hat'])
async def handle_teg_reserve_hat(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admin_or_owner(chat_id, user_id):
        return

    # Извлечение текста после команды
    text_after_command = message.get_args()

    # Получаем всех пользователей, у кого chat_id совпадает и столбец reserve пустой
    users = db.get_users_by_chat_id_with_empty_reserve(chat_id)

    if not users:
        return  # Убираем сообщение, если нет пользователей

    for user in users:
        try:
            user_id = user[0]  # ID пользователя
            username = user[1]  # Username пользователя

            # Формируем сообщение с тегом
            if username:
                tag_message = f"@{username}"
            else:
                tag_message = f"{user[2]}"

            # Добавляем текст после команды, если он есть
            if text_after_command:
                tag_message = f"{tag_message} {text_after_command}"

            await bot.send_message(chat_id, tag_message)
            logging.info(f"Тегнул пользователя: {username if username else user[2]}")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    # Логируем команду
    await log_to_chat(f"Команда /teg_reserve_hat выполнена пользователем {user_id}. Тегнул пользователей в чате {chat_id}.")

# Обработка команды /teg_reserve_li
@dp.message_handler(commands=['teg_reserve_li'])
async def handle_teg_reserve_li(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admin_or_owner(chat_id, user_id):
        return

    # Извлечение текста после команды
    text_after_command = message.get_args()

    # Получаем всех пользователей, у кого chat_id совпадает и столбец reserve пустой
    users = db.get_users_by_chat_id_with_empty_reserve(chat_id)

    if not users:
        return

    for user in users:
        try:
            user_id = user[0]  # ID пользователя
            username = user[1]  # Username пользователя

            # Формируем сообщение с тегом
            if username:
                tag_message = f"@{username}"
            else:
                tag_message = f"{user[2]}"

            # Добавляем текст после команды, если он есть
            if text_after_command:
                tag_message = f"{tag_message} {text_after_command}"

            await bot.send_message(user_id, tag_message)  # Отправляем личное сообщение
            logging.info(f"Тегнул пользователя: {username if username else user[2]} в личных сообщениях.")
        except Exception as e:
            logging.error(f"Ошибка при отправке личного сообщения пользователю {user_id}: {e}")

    # Логируем команду
    await log_to_chat(f"Команда /teg_reserve_li выполнена пользователем {user_id}. Тегнул пользователей в личные сообщения.")

# Команда /rezerv_ba
@dp.message_handler(commands=['rezerv_ba'])
async def rezerv_ba_command(message: types.Message):
    chat_id_input = message.get_args()  # Получаем аргументы команды
    user_id = message.from_user.id  # Получаем ID пользователя

    # Проверка наличия chat_id в базе данных
    available_chats = db.get_all_chat_ids()  # Получаем все chat_id
    available_chat_ids = [chat[0] for chat in available_chats]  # Извлекаем только chat_id
    available_chat_names = [db.get_chat_name(chat[0]) for chat in available_chats]  # Получаем названия чатов

    # Создаем список chat_id и chat_name
    available_chats_list = "\n".join(f"<code>{chat[0]}</code> - {available_chat_names[i]}" for i, chat in enumerate(available_chats))

    # Проверяем, совпадает ли введенный chat_id с существующими
    if not any(chat_id_input in chat[0] for chat in available_chats):
        await message.answer(f"Доступные CHAT_ID:\n{available_chats_list}", parse_mode='HTML')
        return

    # Получаем пользователей с указанным chat_id
    users = db.get_users_for_spisok(chat_id_input)

    # Формируем сообщение с пользователями
    if users:
        users_list = "\n".join(
            f"{user[0] if user[0] else ''} {user[1] if user[1] else ''} - Числа: {user[2] if user[2] else 'Пусто'} - Дата: {user[3] if user[3] else 'Пусто'}"
            for user in users
        )
        await message.answer(f"Список пользователей с указанным CHAT_ID:\n{users_list}")
        await log_to_chat(f"Команда /rezerv_ba выполнена пользователем {user_id}.")
    else:
        await message.answer("Нет пользователей с указанным chat_id.")


# Функция для сброса значений reserve для всех пользователей каждые 24 часа
async def reset_reserves_periodically():
    global reset_task
    while True:
        await asyncio.sleep(86400)  # Ждем 24 часа
        db.reset_all_user_reserves()  # Сбрасываем резерв
        logging.info("Все резервные значения были сброшены.")

@dp.message_handler(commands=['reserv_000r'])
async def handle_reserv_reset(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await is_admin_or_owner(chat_id, user_id):
        return
        
    global reset_task

    # Проверка, что команда отправлена в личных сообщениях
    if message.chat.type == types.ChatType.PRIVATE:
        db.reset_all_user_reserves()  # Обнуляем столбец reserve

        if reset_task:
            reset_task.cancel()  # Отменяем предыдущий таймер

        reset_task = asyncio.create_task(reset_reserves_periodically())  # Запускаем таймер заново
        await message.answer("Все резервные значения были обнулены и таймер сброса запущен заново.")
    else:
        await message.answer("Эта команда может быть использована только в личных сообщениях.")

# Функция для конвертации времени из строки в секунды
def parse_time_input(time_str):
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, time_str)
    
    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()

@dp.message_handler(commands=['reserv_000r'])
async def handle_reserv_reset(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not await is_admin_or_owner(chat_id, user_id):
        return
        
    global reset_task

    # Проверка, что команда отправлена в личных сообщениях
    if message.chat.type == types.ChatType.PRIVATE:
        db.reset_all_user_reserves()  # Обнуляем столбец reserve

        if reset_task:
            reset_task.cancel()  # Отменяем предыдущий таймер

        reset_task = asyncio.create_task(reset_reserves_periodically())  # Запускаем таймер заново
        await message.answer("Все резервные значения были обнулены и таймер сброса запущен заново.")

        # Логируем команду
        await log_to_chat(f"Команда /reserv_000r выполнена пользователем {user_id}.")
    else:
        await message.answer("Эта команда может быть использована только в личных сообщениях.")

# Обработчик команд /xil1, /xil2, /xil3
@dp.message_handler(commands=['xil1', 'xil2', 'xil3'])
async def handle_xil(message: types.Message):
    try:
        command = message.get_command()
        user_id = message.from_user.id
        chat_id = message.chat.id

        # Получаем время из команды
        time_input = message.get_args()
        delay_seconds = parse_time_input(time_input)
        
        if delay_seconds is None:
            await message.reply("Неверный формат времени. Используйте что-то вроде 1h 5m 30s.")
            return
        
        await log_to_chat(f"Команда {command} запущена пользователем {user_id} с задержкой {time_input}.")
        # Задержка перед напоминанием
        await asyncio.sleep(delay_seconds)
        
        # Отправка сообщения по истечении времени
        await bot.send_message(chat_id, f"@{message.from_user.username}, тачка отхилилась!")
        
        # Логируем команду
        await log_to_chat(f"Команда {command} выполнена пользователем {user_id} с задержкой {time_input}.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")
        await log_to_chat(f"Ошибка при выполнении команды {command} пользователем {user_id}: {e}")

@dp.message_handler(commands=['igrok_ap'])
async def handle_igrok_ap(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Проверка на администраторские права
    if not await is_admin_or_owner(chat_id, user_id):
        return

    command_parts = message.text.split()
    
    if len(command_parts) < 2:
        await message.reply("Пожалуйста, укажите @username пользователя.")
        return
    
    username = command_parts[1].lstrip('@')

    user = db.get_user_by_username(username)

    if user:
        db.update_user_status(user[0], "vip")  # Меняем статус на 'vip'
        await message.reply(f"Пользователь @{username} успешно обновлен до статуса VIP.")
        
        # Логируем команду
        await log_to_chat(f"Пользователь @{username} обновлен до статуса VIP пользователем {user_id}.")
    else:
        await message.reply(f"Пользователь @{username} не найден в базе данных.")

@dp.message_handler(commands=['igrok_off'])
async def handle_igrok_off(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Проверка на администраторские права
    if not await is_admin_or_owner(chat_id, user_id):
        return

    command_parts = message.text.split()

    if len(command_parts) < 2:
        await message.reply("Пожалуйста, укажите @username пользователя.")
        return

    username = command_parts[1].lstrip('@')

    user = db.get_user_by_username(username)

    if user:
        db.update_user_status(user[0], "user")  # Меняем статус на 'user'
        await message.reply(f"Пользователь @{username} успешно обновлен до статуса USER.")
        
        # Логируем команду
        await log_to_chat(f"Пользователь @{username} обновлен до статуса USER пользователем {user_id}.")
    else:
        await message.reply(f"Пользователь @{username} не найден в базе данных.")

# Обработка команды /reserve
@dp.message_handler(commands=['reserve'])
async def handle_reserve(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем, нужно ли сбросить значение
    db.check_and_reset_reserve(user_id)

    command_parts = message.text.split(maxsplit=1)
    
    # Проверяем, что пользователь ввел 1-3 цифры от 0 до 6
    if len(command_parts) == 2 and len(command_parts[1]) <= 3 and all(c in '0123456' for c in command_parts[1]):
        reserve_value = command_parts[1]
        
        # Сохраняем новое значение
        db.update_user_reserve(user_id, reserve_value)

        # Запускаем асинхронную задачу для сброса значения через 6 часов
        await asyncio.sleep(21600)  # Ждем 6 часов (21600 секунд)
        db.reset_user_reserve(user_id)  # Сбрасываем значение
        
        # Логируем команду
        await log_to_chat(f"Пользователь {user_id} установил резервное значение на {reserve_value}.")
    else:
        await message.reply("Пожалуйста, укажите 1-3 цифры от 0 до 6 после команды, например: /reserve 012 или /reserve 1.")

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    chat_id = message.chat.id
    chat_name = message.chat.title  # Извлекаем название чата

    # Проверяем, является ли это личный чат
    if message.chat.type == 'private':
        logging.info(f"Пользователь {first_name} @{username} отправляет сообщение в личном чате, не добавляется в базу данных.")
        return

    # Проверяем, существует ли пользователь уже в базе данных
    if not db.user_exists(user_id):
        db.add_user(user_id, username, first_name, last_name, chat_id)
        logging.info(f"Пользователь добавлен в базу данных: {first_name} @{username}")
        
        # Логируем добавление пользователя
        await log_to_chat(f"Пользователь {first_name} @{username} добавлен в базу данных.")
    else:
        # Получаем текущие данные пользователя из базы данных
        existing_user_data = db.get_user_data(user_id)

        # Проверяем, отличается ли информация о пользователе (username, first_name, last_name)
        user_data_updated = False
        if existing_user_data['username'] != username:
            user_data_updated = True
            logging.info(f"Username обновлен с {existing_user_data['username']} на {username}.")
        if existing_user_data['first_name'] != first_name:
            user_data_updated = True
            logging.info(f"First_name обновлен с {existing_user_data['first_name']} на {first_name}.")
        if existing_user_data['last_name'] != last_name:
            user_data_updated = True
            logging.info(f"Last_name обновлен с {existing_user_data['last_name']} на {last_name}.")

        # Обновляем данные пользователя в базе, если они изменились
        if user_data_updated:
            db.update_user(user_id, username, first_name, last_name)
            logging.info(f"Данные пользователя {first_name} @{username} обновлены в базе данных.")
            
            # Логируем обновление пользователя
            await log_to_chat(f"Данные пользователя {first_name} @{username} обновлены в базе данных.")

        existing_chat_ids = db.get_user_chat_ids(user_id)

        # Проверяем, если текущий chat_id уже есть в списке, не добавляем его снова
        if str(chat_id) in existing_chat_ids:
            logging.info(f"CHAT_ID {chat_id} уже существует для пользователя {first_name} @{username}.")
        else:
            # Если chat_id не существует, добавляем его
            existing_chat_ids.append(str(chat_id))
            db.update_user_chat_ids(user_id, existing_chat_ids)
            logging.info(f"CHAT_ID {chat_id} добавлен для пользователя {first_name} @{username}.")
            
            # Логируем добавление chat_id
            await log_to_chat(f"CHAT_ID {chat_id} добавлен для пользователя {first_name} @{username}.")

    # Проверяем, существует ли chat_id в таблице chats
    if not db.chat_exists(chat_id):
        db.add_chat(chat_id, chat_name)  # Передаем название чата
        logging.info(f"Chat ID {chat_id} с названием '{chat_name}' добавлен в таблицу.")
        
        # Логируем добавление чата
        await log_to_chat(f"Chat ID {chat_id} с названием '{chat_name}' добавлен в таблицу.")



# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
