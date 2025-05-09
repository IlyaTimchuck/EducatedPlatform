from aiogram.types import CallbackQuery
from aiogram import Router
from app.bot.infrastructure.api.google_table import google_client
import app.bot.infrastructure.database as db


router = Router()
@router.callback_query(lambda c: c.data.startswith('cancel_deleting') or c.data.startswith('confirm_deleting'))
async def process_deleting_user(callback_query: CallbackQuery):
    action, user_id = callback_query.data.split(':')
    user_id = int(user_id)
    if action == 'cancel_deleting':
        user_data = await db.users.get_data_user(user_id)
        course_title = await db.courses.get_course_title(user_data['course_id'])
        timezone = (await db.deadlines.get_timezones())[user_data['timezone_id']]
        user_data_for_table = [user_data['real_name'], user_data['telegram_username'], course_title, user_id, timezone,
                               user_data['date_of_joining'], 'student', 3]
        await google_client.add_user_in_table(*user_data_for_table)
        await callback_query.answer('Удаление было отменено. Все данные пользователя восстановлены')
        await callback_query.message.delete()
    else:
        await db.users.delete_all_user_data(user_id)
        await google_client.delete_deadlines_for_user(user_id)
        await callback_query.answer('Пользователь успешно удален')
        await callback_query.message.delete()