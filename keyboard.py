from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import calendar


def choose_parameters_task(deadline):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Автоматическая проверка', callback_data=f'verif:auto:{deadline}'),
                          InlineKeyboardButton(text='Ручная проверка', callback_data=f'verif:manual:{deadline}')]
                         ])
    return keyboard


def generate_calendar(year: int, month: int) -> InlineKeyboardMarkup:
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
                                 callback_data=f'select_day:{year}:{month}:{day}')
            for day in week])
    return builder.as_markup()


def to_change_block(current_block):
    change_block_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Предыдущий блок', callback_data=f'reduce_block:{current_block}'),
         InlineKeyboardButton(text='Следующий блок', callback_data=f'increase_block:{current_block}')],
        [InlineKeyboardButton(text='Подтвердить выбор', callback_data=f'confirm_block:{current_block}')],
        [InlineKeyboardButton(text='Назад', callback_data='back_admin')]
    ])
    return change_block_buttons


async def choose_course_inline():
    builder = InlineKeyboardBuilder()
    data = await db.get_list_courses()
    for course in data:
        builder.add(InlineKeyboardButton(text=course, callback_data=f'choose_course:{course}'))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def choose_course_reply():
    builder = ReplyKeyboardBuilder()
    data = await db.get_list_courses()
    builder.add(KeyboardButton(text='Создать новый'))
    for course in data:
        builder.add(KeyboardButton(text=course))

    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


back_button_student = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_student')]
])

back_button_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_admin')]
])

command_menu_student = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Список занятий', callback_data='lesson_list')],
    [InlineKeyboardButton(text='Открыть последнее занятие', callback_data='last_lesson')],
    [InlineKeyboardButton(text='Посмотреть историю жизней', callback_data='list_lives')],
])

command_menu_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить урок', callback_data='add_lesson')],
    [InlineKeyboardButton(text='Добвить пользователей', callback_data='add_users')]
])

send_homework_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Редактировать введённые данные', callback_data='change_homework')],
    [InlineKeyboardButton(text='Отправить домашнюю работу', callback_data='send_homework')]
])

confirm_task = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Редактировать', callback_data='finish_task:edit_task'),
     InlineKeyboardButton(text='Подтвердить', callback_data='finish_task:confirm_task')]
])