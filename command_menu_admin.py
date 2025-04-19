from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message
from aiogram import Router, F
from datetime import datetime
from bot_instance import bot, dp
from google_table import google_client

import calendar
import state as st
import database as db
import keyboard as kb

router = Router()


@router.callback_query(lambda c: c.data.startswith('cancel_deleting') or c.data.startswith('confirm_deleting'))
async def process_deleting_user(callback_query: CallbackQuery):
    action, user_id = callback_query.data.split(':')
    user_id = int(user_id)
    if action == 'cancel_deleting':
        user_data = await db.get_data_user(user_id)
        course_title = await db.get_course_title(user_data['course_id'])
        timezone = (await db.get_timezones())[user_data['timezone_id']]
        user_data_for_table = [user_data['real_name'], user_data['telegram_username'], course_title, user_id, timezone, user_data['date_of_joining'], 'student', 3]
        await google_client.add_user_in_table(*user_data_for_table)
        await callback_query.answer('Удаление было отменено. Все данные пользоателя восстановлены')
        await callback_query.message.delete()
    else:
        await db.delete_all_user_data(user_id)
        await callback_query.answer('Пользователь успешно удален')
        await callback_query.message.delete()
