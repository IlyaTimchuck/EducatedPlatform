from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import app.bot.infrastructure.database as db
import calendar


async def choose_parameters_task(deadline) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Нет', callback_data=f"verif:0:{deadline}"),
                          InlineKeyboardButton(text='Да', callback_data=f"verif:1:{deadline}")]
                         ])
    return keyboard


async def generate_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="\u2190", callback_data=f"prev_month:{year}:{month}"),
        InlineKeyboardButton(text=f"{year}, {calendar.month_name[month]}", callback_data="ignore"),
        InlineKeyboardButton(text="\u2192", callback_data=f"next_month:{year}:{month}")
    )
    day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    builder.row(*[InlineKeyboardButton(text=day, callback_data='ignore') for day in day_names])
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        builder.row(*[
            InlineKeyboardButton(text=str(day) if day != 0 else ' ',
                                 callback_data=f"select_day:{year}:{month}:{day}")
            for day in week])
    return builder.as_markup()


async def to_change_block(current_block):
    change_block_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Предыдущий блок', callback_data=f"reduce_block:{current_block}"),
         InlineKeyboardButton(text='Следующий блок', callback_data=f"increase_block:{current_block}")],
        [InlineKeyboardButton(text='Подтвердить выбор', callback_data=f"confirm_block:{current_block}")],
        [InlineKeyboardButton(text='Назад', callback_data='back_admin')]
    ])
    return change_block_buttons


async def choose_course_inline(for_add_task: bool):
    """Используется для добавления задания"""
    builder = InlineKeyboardBuilder()
    courses = await db.courses.get_list_courses()
    callback_data = 'course_selection_for_task_creation' if for_add_task else 'course_selection_for_user_metrics'
    for course in courses:
        builder.add(
            InlineKeyboardButton(text=course['course_title'], callback_data=f"{callback_data}:{course['course_id']}"))
    builder.row(InlineKeyboardButton(text='Назад', callback_data='back_admin'))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


confirm_new_block_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отменить', callback_data='cancel_update_block'),
     InlineKeyboardButton(text='Подтвердить', callback_data='confirm_new_block')]
])

availability_files_task = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Нет', callback_data='availability_files:Нет'),
     InlineKeyboardButton(text='Да', callback_data='availability_files:Да')]
])

confirm_task = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Редактировать', callback_data='finish_task:edit_task'),
     InlineKeyboardButton(text='Подтвердить', callback_data='finish_task:confirm_task')]
])

send_exercise = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отправить данные из таблицы в базу данных', callback_data='send_exercise')]
])
