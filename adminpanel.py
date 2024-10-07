from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db

# Define a list of admin user IDs
ADMIN_USER_IDS = [6748680385, 6213428571]  # Replace with actual admin user IDs

MAX_MESSAGE_LENGTH = 4096  # Максимальная длина сообщения

async def send_long_message(bot, chat_id, text):
    if len(text) <= MAX_MESSAGE_LENGTH:
        await bot.send_message(chat_id, text)
    else:
        parts = [text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
        for part in parts:
            await bot.send_message(chat_id, part)

async def admin_panel(message: types.Message):
    if message.from_user.id in ADMIN_USER_IDS:
        num_users = db.get_num_users()
        button_text = f"Пользователи ({num_users})"
        await message.answer("Добро пожаловать в админ-панель!\nВыберите действие:",
                             reply_markup=InlineKeyboardMarkup().add(
                                 InlineKeyboardButton(button_text, callback_data="users")))
    else:
        await message.answer("Пожалуйста, начните с команды /start.")

async def process_users_button(callback_query: types.CallbackQuery):
    if callback_query.from_user.id in ADMIN_USER_IDS:
        users = db.get_all_users()
        if users:
            users_list = "\n".join([f"ID: {user[0]}, Username: @{user[1]}, Full Name: {user[2] if user[2] else ''} {user[3] if user[3] else ''}, Refs: {user[4]}" for user in users])
            message_text = f"Список пользователей:\n{users_list}"
            await send_long_message(callback_query.bot, callback_query.message.chat.id, message_text)
        else:
            await callback_query.message.answer("В базе данных нет пользователей.")
    else:
        await callback_query.answer("Извините, у вас нет доступа к этой функции.")



