from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message

import app.bot.infrastructure.database as db
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


async def mapping_block_list(user_id: int, course_id: int, admin_connection: bool):
    data = await db.blocks.get_blocks(course_id)
    builder = InlineKeyboardBuilder()
    for block in data:
        builder.row(InlineKeyboardButton(text=f"{block} блок",
                                         callback_data=f"open_block:{data[block]}"))
    builder.row(*[InlineKeyboardButton(text='Назад ↩️',
                                       callback_data=f"open_metric_user:{user_id}" if admin_connection else 'back_student')])
    return builder.as_markup()


async def mapping_list_tasks(user_id: int, block_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tasks = await db.tasks.get_list_tasks(block_id)
    for task_title in tasks:
        task_id = tasks[task_title]
        task_status = await db.progress.mapping_task_status(user_id, task_id)
        builder.row(
            *[InlineKeyboardButton(text=f"{task_title}{task_status}",
                                   callback_data=f"open_task:{task_id}:0")])
    builder.row(*[InlineKeyboardButton(text='Назад ↩️', callback_data='block_list')])
    return builder.as_markup()


async def mapping_task(block_id, file_work_info: dict[bool:bool],
                       abstract_retrieved: bool = False) -> InlineKeyboardMarkup:
    keyboard_buttons = [
        [InlineKeyboardButton(text='Домашняя работа', callback_data='open_homework')]
    ]
    if not abstract_retrieved:
        keyboard_buttons.append(
            [InlineKeyboardButton(text='Конспект урока', callback_data='send_abstract')]
        )
    if file_work_info['file_work'] and (not file_work_info['file_work_retrieved']):
        keyboard_buttons.append(
            [InlineKeyboardButton(text='Получить свой рабочий файл', callback_data='send_file_work')]
        )
    keyboard_buttons.append([
        InlineKeyboardButton(text='↩️ Назад', callback_data=f"open_block_from_homework:{block_id}"),
        InlineKeyboardButton(text='В главное меню 🏠', callback_data='back_student')
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


async def mapping_homework(quantity_exercise: int, current_exercise: int, file_work: bool,
                           admin_connection: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_exercise == 1:
        builder.add(
            InlineKeyboardButton(text=f"{current_exercise}/{quantity_exercise}", callback_data='open_list_exercises'),
            InlineKeyboardButton(text='\u2192', callback_data=f"next_exercise:{current_exercise + 1}"))
        builder.adjust(2)
    elif current_exercise == quantity_exercise:
        builder.add(InlineKeyboardButton(text="\u2190", callback_data=f"prev_exercise:{current_exercise - 1}"),
                    InlineKeyboardButton(text=f"{current_exercise}/{quantity_exercise}",
                                         callback_data='open_list_exercises'))
        builder.adjust(2)
    else:
        builder.add(
            InlineKeyboardButton(text="\u2190", callback_data=f"prev_exercise:{current_exercise - 1}"),
            InlineKeyboardButton(text=f"{current_exercise}/{quantity_exercise}", callback_data='open_list_exercises'),
            InlineKeyboardButton(text='\u2192', callback_data=f"next_exercise:{current_exercise + 1}"))
        builder.adjust(3)

    if not admin_connection:
        if file_work:
            builder.row(
                *[InlineKeyboardButton(text='Перейти к отправке файла', callback_data='get_file_work')])
        else:
            builder.row(*[InlineKeyboardButton(text='Завершить выполнение работы', callback_data='complete_homework')])
    builder.row(*[InlineKeyboardButton(text='↩️ Вернуться назад', callback_data='back_to_task')])
    return builder.as_markup()


async def mapping_list_exercises(state_data: dict, decides: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    user_id = state_data.get('user_id')
    task_id = state_data['task_data']['task_id']
    homework = state_data['homework']
    if decides:
        results = state_data.get('results', {})
        for exercise_number in homework:
            result_status = results.get(exercise_number, {}).get('status_input_answer', '⌛')
            builder.add(InlineKeyboardButton(
                text=f"{exercise_number} задание {result_status}",
                callback_data=f"open_exercise:{exercise_number}"
            ))
    else:
        progress_solving = await db.progress.get_progress_user(user_id, task_id)
        for exercise_number in homework:
            if exercise_number in progress_solving:
                status = '⌛' if progress_solving[exercise_number]['input_answer'] is None else \
                    progress_solving[exercise_number]['exercise_status']
            else:
                status = '⌛'  # Или любой другой значок, если данных нет

            builder.add(InlineKeyboardButton(
                text=f"{exercise_number} задание {status}",
                callback_data=f"open_exercise:{exercise_number}"
            ))

    builder.adjust(1)
    return builder.as_markup()


async def start_the_task_from_the_reminder(course_id: int, task_id: int) -> InlineKeyboardMarkup:
    button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Приступить к выполнению задания',
                              callback_data=f"open_task:{course_id}:{task_id}:1")]
    ])
    return button


back_to_homework = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Вернуться к домашней работе', callback_data='open_homework')]
])

confirm_completing_work_file = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Вернуться назад', callback_data='open_homework'),
     InlineKeyboardButton(text='Завершить', callback_data='complete_homework')]
])

send_homework_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Редактировать введённые данные', callback_data='change_homework')],
    [InlineKeyboardButton(text='Отправить домашнюю работу', callback_data='send_homework')]
])

# ——— ОГРАНИЧЕНИЕ ДОСТУПА ПРИ ОТСУТСВИИ life ———
block_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Попробовать еще раз 🔁', callback_data='attempt_to_log_in')]
])

# ——— ЗАПРОС ГЕОЛОКАЦИИ ПРИ РЕГИСТРАЦИИ———
location_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
