from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message

import app.bot.infrastructure.database as db
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


async def mapping_list_users(course_id: int):
    builder = InlineKeyboardBuilder()
    list_users = await db.users.get_users_by_course(course_id)
    for user_data in list_users:
        builder.row(InlineKeyboardButton(text=user_data['real_name'],
                                         callback_data=f"open_metric_user:{user_data['user_id']}"))
    builder.row(InlineKeyboardButton(text='Назад', callback_data='get_list_courses'))
    return builder.as_markup()


async def get_more_metric(course_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Открыть последний решенный урок',
                              callback_data='open_task')],
        [InlineKeyboardButton(text='Перейти к урокам пользователя',
                              callback_data='block_list')],
        [InlineKeyboardButton(text='Назад', callback_data=f"course_selection_for_user_metrics:{course_id}")]
    ])
    return keyboard


async def confirm_deleting_user(user_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Отменить', callback_data=f"cancel_deleting:{user_id}"),
         InlineKeyboardButton(text='Подтвердить', callback_data=f"confirm_deleting:{user_id}")]
    ])
    return keyboard


async def choose_course_reply():
    """Используется для добавления списка пользователей"""
    builder = ReplyKeyboardBuilder()
    courses = await db.courses.get_list_courses()
    builder.add(KeyboardButton(text='Создать новый'))
    for course in courses:
        builder.add(KeyboardButton(text=course['course_title']))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
