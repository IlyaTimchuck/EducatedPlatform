from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message
import app.bot.infrastructure.database as db


async def send_command_menu(user_id: int):
    user_data = await db.users.get_data_user(user_id)
    if user_data['role'] == 'student':
        command_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Список занятий', callback_data='block_list')],
            [InlineKeyboardButton(text='Открыть последнее занятие', callback_data='open_task')],
            [InlineKeyboardButton(text='Посмотреть историю жизней', callback_data='list_lives')],
        ])
        lives = user_data['lives']
        deadline_today = await db.deadlines.get_today_deadline_for_keyboard(user_id)
        text_message = f'Текущее количество жизней: {lives * '❤️'}\n'
        if deadline_today:
            text_message += f'Дедлайны сегодня: {', '.join(task['task_title'] for task in deadline_today)}\n'
        else:
            text_message += 'Дедлайны сегодня: -\n'
        metric_user = await db.metrics.get_metric_user(user_id)
        right_answers = metric_user['right_answers']
        total_exercises = metric_user['total_exercises']
        quotient = str(round((right_answers / total_exercises)) * 100) + '%' if total_exercises != 0 else '-'
        text_message += f'Всего решено заданий на курсе: {metric_user['right_answers']}\nПроцент выполненных заданий: {quotient}'
        return text_message, command_menu
    elif user_data['role'] == 'admin':
        command_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Добавить урок', callback_data='add_lesson')],
            [InlineKeyboardButton(text='Контроль успеваемости', callback_data='get_list_courses')],
            [InlineKeyboardButton(text='Добавить пользователей', callback_data='add_users')]
        ])
        text_message = 'Распознал тебя как админа'
        return text_message, command_menu


back_button_student = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_student')]
])

back_button_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_admin')]
])




