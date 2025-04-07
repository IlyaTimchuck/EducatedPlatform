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


@router.callback_query(F.data == 'add_users')
async def process_add_users(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer('Выбери курс', reply_markup=await kb.choose_course_reply())
    await state.set_state(st.AddUsers.choose_course)


@router.callback_query(F.data == 'add_lesson')
async def process_add_lesson(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(f'Для добавления домашнего задания выбери курс',
                                           reply_markup=await kb.choose_course_inline())


@router.callback_query(lambda c: c.data.startswith('choose_course'))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.set_state(st.AddTask.choose_course)
    course_name = callback_query.data.split(":")[-1]
    course_id = await db.get_course_id(course_name)
    current_block = await db.get_blocks(course_id, current=True)
    await state.update_data(course_id=course_id, current_block=current_block)
    await callback_query.message.edit_text(
        f'Выбери блок\n\nТекущий выбор: {current_block} блок',
        reply_markup=await kb.to_change_block(current_block))


@router.callback_query(
    lambda c: c.data.startswith("increase_block") or c.data.startswith("reduce_block") or c.data.startswith(
        "confirm_block"))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    action, current_value = callback_query.data.split(":")
    selected_block = int(current_value)
    if action == "increase_block":
        selected_block += 1
    elif action == "reduce_block" and selected_block != 1:
        selected_block -= 1
    elif action == 'confirm_block':
        state_data = await state.get_data()
        course_id = state_data['course_id']
        block_id = await db.check_block_exists(course_id, selected_block)
        await state.update_data(selected_block=selected_block)
        if block_id:
            year = datetime.now().year
            month = datetime.now().month
            await state.set_state(st.AddTask.choose_options)
            await callback_query.message.edit_text('Выбери дату дедлайна',
                                                   reply_markup=await kb.generate_calendar(year, month))
            await state.update_data(block_id=block_id)
        else:
            await callback_query.message.edit_text(
                f'Твой выбор: {selected_block}\nТекущий блок на курсе: {state_data['current_block']}\n\nНачать новый блок и обновить всем пользователям жизни?',
                reply_markup=kb.confirm_new_block_keyboard)
    new_text = f'Выбери блок\n\nТекущий выбор: {selected_block} блок'
    if callback_query.message.text != new_text:
        await callback_query.message.edit_text(text=f'Выбери блок\n\nТекущий выбор: {selected_block} блок',
                                               reply_markup=await kb.to_change_block(selected_block))


@router.callback_query(lambda c: c.data == 'cancel_update_block' or c.data == 'confirm_new_block')
async def confirm_new_block(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data
    state_data = await state.get_data()
    if action == 'cancel_update_block':
        await callback_query.message.edit_text(
            f'Выбери блок\n\nТекущий выбор: {state_data['current_block']} блок',
            reply_markup=await kb.to_change_block(state_data['current_block']))
    elif action == 'confirm_new_block':
        year = datetime.now().year
        month = datetime.now().month
        block_id = await db.create_block(state_data['course_id'], state_data['selected_block'])
        await db.update_lives(state_data['course_id'])
        await state.update_data(block_id=block_id)
        await state.set_state(st.AddTask.choose_options)
        await callback_query.message.edit_text('Выбери дату дедлайна',
                                               reply_markup=await kb.generate_calendar(year, month))


@router.callback_query(lambda c: c.data.startswith('prev_month') or c.data.startswith('next_month'))
async def month(callback_query: CallbackQuery):
    action, year, month = callback_query.data.split(":")
    year, month = int(year), int(month)
    if action == "prev_month":
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
    elif action == "next_month":
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    new_markup = await kb.generate_calendar(year, month)
    await callback_query.message.edit_reply_markup(reply_markup=new_markup)


@router.callback_query(lambda c: c.data.startswith("select_day"))
async def select_day(callback_query: CallbackQuery):
    _, year, month, day = callback_query.data.split(":")
    await callback_query.message.edit_text(
        f"Дата дедлайна: {day} {calendar.month_name[int(month)]} {year}\nТребуется файл решений от ученика:",
        reply_markup=await kb.choose_parameters_task(f'{year}-{month}-{day}'))


@router.callback_query((lambda c: c.data.startswith('verif')))
async def choose_verification(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    _, file_work, deadline_date = callback_query.data.split(':')
    file_work = bool(file_work)
    day, month, year = deadline_date.split('-')
    await state.update_data(file_work=file_work, deadline=deadline_date)
    await callback_query.message.edit_text(
        f'''Дата дедлайна: {day} {calendar.month_name[int(month)]} {year}\nТребовать файл решений: {'Да' if file_work else 'Нет'}\nФайлы в заданиях:''',
        reply_markup=kb.availability_files_task)


@router.callback_query(lambda c: c.data.startswith('availability_files'))
async def process_availability_files(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    availability_files = callback_query.data.split(':')[-1]
    await state.update_data(availability_files=True if availability_files == 'Да' else False)
    current_text = callback_query.message.text
    new_text = current_text + f' {availability_files}'
    await callback_query.message.edit_text(text=new_text, reply_markup=kb.confirm_task)


@router.callback_query(lambda c: c.data.startswith('finish_task'))
async def process_finish_task(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    action = callback_query.data.split(':')[-1]
    if action == 'edit_task':
        year = datetime.now().year
        month = datetime.now().month
        await callback_query.message.edit_text(f'Выбери дату дедлайна',
                                               reply_markup=await kb.generate_calendar(year, month))
    elif action == 'confirm_task':
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.answer('Отправь мне название урока')
        await state.set_state(st.AddTask.get_task_title)


@router.message(st.AddUsers.choose_course)
async def process_choose_course(message: Message, state: FSMContext):
    if message.text == 'Создать новый':
        await message.answer('Отправь мне название курса')
        await state.set_state(st.AddUsers.get_course_tittle)
    else:
        await state.update_data(course_tittle=message.text)
        await message.answer('Отправь мне список пользователей')
        await state.set_state(st.AddUsers.get_list_users)


@router.message(st.AddUsers.get_course_tittle)
async def process_get_course_tittle(message: Message, state: FSMContext):
    await state.update_data(course_tittle=message.text)
    await db.create_course(message.text)
    await message.answer('Отправь мне список пользователей')
    await state.set_state(st.AddUsers.get_list_users)


@router.message(st.AddUsers.get_list_users)
async def process_get_list_users(message: Message, state: FSMContext):
    list_users = message.text.split('\n')
    data = await state.get_data()
    course_id = await db.get_course_id(data['course_tittle'])
    await db.add_users(list_users, course_id)
    _, keyboard = await kb.send_command_menu(message.from_user.id)
    await message.answer('Пользователи были успешно добавлены', reply_markup=keyboard)


@router.message(st.AddTask.get_task_title)
async def process_get_task_title(message: Message, state: FSMContext):
    await state.update_data(task_title=message.text)
    await message.answer('Название было успешно записано. Теперь отправь мне видеозапись урока')
    await state.set_state(st.AddTask.get_video)


@router.message(st.AddTask.get_video)
async def process_get_video(message: Message, state: FSMContext):
    await state.update_data(video_id=message.video.file_id)
    availability_files = await state.get_value('availability_files')
    if availability_files:
        await message.answer('Видео было успешно записано. Теперь отправь ссылку на репозиторий с файлами')
        await state.set_state(st.AddTask.get_files)
    else:
        await message.answer('Видео было успешно записано. Теперь отправь конспект урока')
        await state.set_state(st.AddTask.get_abstract)


@router.message(st.AddTask.get_files)
async def process_get_files(message: Message, state: FSMContext):
    await state.update_data(link_files=message.text)
    await message.answer('Ссылка была успешно записана. Теперь отправь конспект урока')
    await state.set_state(st.AddTask.get_abstract)


@router.message(st.AddTask.get_abstract)
async def process_get_abstract(message: Message, state: FSMContext):
    await state.update_data(abstract_id=message.document.file_id)
    await message.answer('Добавь условия и ответы в гугл таблицу', reply_markup=kb.send_exercise)
    await state.set_state(st.AddTask.verification)


@router.callback_query(F.data == 'send_exercise')
async def process_send_exercise(callback_query: CallbackQuery, state: FSMContext):
    """Создаем task. Проверяем, есть ли в задании автопроверка."""
    await callback_query.answer()
    state_data = await state.get_data()
    link_files = state_data.get('link_files', None)
    task_id = await db.add_task(state_data['task_title'], state_data['block_id'], state_data['file_work'],
                                state_data['video_id'], state_data['abstract_id'], link_files,
                                state_data['deadline'])
    exercises = await google_client.get_exersice()
    for exercise in exercises:
        exercise_condition = exercise[0]
        exercise_answer = exercise[1]
        await db.add_exercise(task_id, exercise_condition, exercise_answer)

    users_by_course = await db.get_users_by_course(state_data['course_id'])
    for user_id in users_by_course:
        notification_about_new_task = await bot.send_message(chat_id=user_id,
                               text=f'Привет! Только что был добавлен новый урок: {state_data['task_title']}\nЧтобы перейти к нему жми на кнопку!',
                               reply_markup=await kb.start_the_task_from_the_reminder(state_data['course_id'],
                                                                                      task_id))
        storage_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
        state = FSMContext(storage=dp.storage, key=storage_key)
        await state.update_data(rnotification_about_new_task_message_id=notification_about_new_task.message_id)