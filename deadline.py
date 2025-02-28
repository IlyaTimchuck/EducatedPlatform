from aiogram import Router
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta


import pytz
import database as db
import keyboard as kb
import logging
import asyncio

router = Router()



async def current_deadline(user_id, lives, new_deadline):
    """
    Обновляет данные пользователя в БД: количество жизней и новый дедлайн.
    """
    # Реализуйте обновление в вашей базе данных
    pass


async def homework_monitor():
    """Фоновая задача, которая проверяет дедлайны домашних заданий."""
    while True:
        logging.info("Запуск проверки дедлайнов домашних заданий.")

        now = datetime.utcnow()

        # Получаем список всех пользователей
        users = await db.get_all_users()
        changed_deadline = await db.get_changed_deadline(...)
        right_decisions = await db.get_right_session(...)
        for user_info in users:
            timezone = datetime.now(user_info['timezone'])
            user_deadline = user_info['deadline']  # Дедлайн должен быть объектом datetime
            if now >= user_deadline:
                # Если задание не выполнено, снимаем жизнь и переносим дедлайн на следующий день
                new_deadline = user_deadline + timedelta(days=1)
                new_lives = user_info['lives'] - 1

                await update_user(user_info['id'], new_lives, new_deadline)
                logging.info(
                    f"Пользователю {user_info['id']} снята жизнь. Новый дедлайн: {new_deadline}"
                )

        await asyncio.sleep(60)
