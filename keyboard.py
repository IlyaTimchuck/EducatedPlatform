from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message

import database as db
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import calendar


async def mapping_block_list(course_id: int):
    data = await db.get_blocks(course_id)
    builder = InlineKeyboardBuilder()
    for block in data:
        builder.row(InlineKeyboardButton(text=f'{block} блок', callback_data=f'open_block:{course_id}:{data[block]}'))
    builder.row(*[InlineKeyboardButton(text='Назад', callback_data='back_student')])
    return builder.as_markup()


async def mapping_list_tasks(user_id: int, course_id: int, block_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tasks = await db.get_list_tasks(block_id)
    for task_title in tasks:
        task_id = tasks[task_title]
        task_status = await db.mapping_task_status(user_id, task_id)
        builder.row(
            *[InlineKeyboardButton(text=f'{task_title}{task_status}',
                                   callback_data=f'open_task:{course_id}:{task_id}:0')])
    return builder.as_markup()


async def mapping_homework(quantity_exercise: int, current_exercise: int, file_work: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_exercise == 1:
        builder.add(
            InlineKeyboardButton(text=f'{current_exercise}/{quantity_exercise}', callback_data='open_list_exercises'),
            InlineKeyboardButton(text='\u2192', callback_data=f'next_exercise:{current_exercise + 1}'))
        builder.adjust(2)
    elif current_exercise == quantity_exercise:
        builder.add(InlineKeyboardButton(text="\u2190", callback_data=f'prev_exercise:{current_exercise - 1}'),
                    InlineKeyboardButton(text=f'{current_exercise}/{quantity_exercise}',
                                         callback_data='open_list_exercises'))
        builder.adjust(2)
    else:
        builder.add(
            InlineKeyboardButton(text="\u2190", callback_data=f'prev_exercise:{current_exercise - 1}'),
            InlineKeyboardButton(text=f'{current_exercise}/{quantity_exercise}', callback_data='open_list_exercises'),
            InlineKeyboardButton(text='\u2192', callback_data=f'next_exercise:{current_exercise + 1}'))
        builder.adjust(3)
    if file_work:
        builder.row(
            *[InlineKeyboardButton(text='Сохранить ответы и перейти к отправке файла', callback_data='get_file_work')])
    else:
        builder.row(*[InlineKeyboardButton(text='Завершить выполнение работы', callback_data='complete_homework')])
    return builder.as_markup()


async def mapping_task(course_id, block_id, abstract_retrieved: bool = False) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [InlineKeyboardButton(text='Домашняя работа', callback_data='open_homework')]
    ]
    if not abstract_retrieved:
        keyboard_buttons.append(
            [InlineKeyboardButton(text='Конспект урока', callback_data='get_abstract')]
        )
    keyboard_buttons.append([
        InlineKeyboardButton(text='Назад', callback_data=f'open_block_from_homework:{course_id}:{block_id}'),
        InlineKeyboardButton(text='В главное меню', callback_data='back_student')
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


async def mapping_list_exercises(state_data: dict, decides: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    task_id = state_data['task_data']['task_id']
    homework = state_data['homework']
    if decides:
        results = state_data.get('results', {})
        for exercise_number in homework:
            result_status = results.get(exercise_number, {}).get('status_input_answer', '⌛')
            builder.add(InlineKeyboardButton(
                text=f'{exercise_number} задание {result_status}',
                callback_data=f'open_exercise:{exercise_number}'
            ))
    else:
        progress_solving = await db.get_progress_user(task_id)
        for exercise_number in homework:
            if exercise_number in progress_solving:
                status = '⌛' if progress_solving[exercise_number]['input_answer'] is None else \
                    progress_solving[exercise_number]['exercise_status']
            else:
                status = '⌛'  # Или любой другой значок, если данных нет

            builder.add(InlineKeyboardButton(
                text=f'{exercise_number} задание {status}',
                callback_data=f'open_exercise:{exercise_number}'
            ))

    builder.adjust(1)
    return builder.as_markup()


async def choose_parameters_task(deadline) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Нет', callback_data=f'verif:0:{deadline}'),
                          InlineKeyboardButton(text='Да', callback_data=f'verif:1:{deadline}')]
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
                                 callback_data=f'select_day:{year}:{month}:{day}')
            for day in week])
    return builder.as_markup()


async def to_change_block(current_block):
    change_block_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Предыдущий блок', callback_data=f'reduce_block:{current_block}'),
         InlineKeyboardButton(text='Следующий блок', callback_data=f'increase_block:{current_block}')],
        [InlineKeyboardButton(text='Подтвердить выбор', callback_data=f'confirm_block:{current_block}')],
        [InlineKeyboardButton(text='Назад', callback_data='back_admin')]
    ])
    return change_block_buttons


async def choose_course_inline():
    """Используется для добавления задания"""
    builder = InlineKeyboardBuilder()
    courses = await db.get_list_courses()
    for course in courses:
        builder.add(
            InlineKeyboardButton(text=course['course_title'], callback_data=f"choose_course:{course['course_title']}"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def choose_course_reply():
    """Используется для добавления списка пользователей"""
    builder = ReplyKeyboardBuilder()
    courses = await db.get_list_courses()
    builder.add(KeyboardButton(text='Создать новый'))
    for course in courses:
        builder.add(KeyboardButton(text=course['course_title']))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def send_command_menu(user_id: int):
    user_data = await db.get_data_user(user_id)
    if user_data['role'] == 'student':
        last_task = await db.get_last_task(user_id)
        callback_data_last_task = f'open_task:{last_task['course_id']}:{last_task['task_id']}:0' if last_task else 'ignore'
        command_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Список занятий', callback_data='block_list')],
            [InlineKeyboardButton(text='Открыть последнее занятие', callback_data=callback_data_last_task)],
            [InlineKeyboardButton(text='Посмотреть историю жизней', callback_data='list_lives')],
        ])
        lives = user_data['lives']
        deadline_today = await db.get_today_deadline_for_keyboard(user_id)
        text_message = f'Текущее количество жизней: {lives * '❤️'}\n'
        if deadline_today:
            text_message += f'Дедлайны сегодня: {', '.join(task['task_title'] for task in deadline_today)}'
        else:
            text_message += 'Дедлайны сегодня: -'
        return text_message, command_menu
    elif user_data['role'] == 'admin':
        command_menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Добавить урок', callback_data='add_lesson')],
            [InlineKeyboardButton(text='Добвить пользователей', callback_data='add_users')]
        ])
        text_message = 'Распознал тебя как админа'
        return text_message, command_menu


async def start_the_task_from_the_reminder(course_id: int, task_id: int) -> InlineKeyboardMarkup:
    button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Приступить к выполнению задания',
                              callback_data=f'open_task:{course_id}:{task_id}:1')]
    ])
    return button


back_button_student = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_student')]
])

back_button_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='back_admin')]
])

send_homework_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Редактировать введённые данные', callback_data='change_homework')],
    [InlineKeyboardButton(text='Отправить домашнюю работу', callback_data='send_homework')]
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

location_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

confirm_new_block_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отменить', callback_data='cancel_update_block'),
     InlineKeyboardButton(text='Подтвердить', callback_data='confirm_new_block')]
])

back_to_homework = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вернуться к домашней работе', callback_data='open_homework')]
])

confirm_completing_work_file = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вернуться назад', callback_data='open_homework'),
     InlineKeyboardButton(text='Завершить', callback_data='complete_homework')]
])
