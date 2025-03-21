from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram import Router, F
from datetime import datetime
from bot_instance import bot
from google_table import get_exersice

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
        f"Дата дедлайна: {day} {calendar.month_name[int(month)]} {year}\nВыбери тип проверки:",
        reply_markup=await kb.choose_parameters_task(f'{year}-{month}-{day}'))


@router.callback_query((lambda c: c.data.startswith('verif')))
async def choose_verification(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    _, verif, deadline_date = callback_query.data.split(':')
    verif = 'Автоматическая проверка' if verif == 'auto' else 'Ручная проверка'
    day, month, year = deadline_date.split('-')
    await state.update_data(verification=verif, deadline=deadline_date)
    await callback_query.message.edit_text(
        f'''Дата дедлайна: {day} {calendar.month_name[int(month)]} {year}\nТип проверки: {verif}\nФайлы в заданиях:''',
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


@router.callback_query(F.data == 'send_exercise')
async def process_send_exercise(callback_query: CallbackQuery, state: FSMContext):
    """Создаем task. Проверяем, есть ли в задании автопроверка."""
    await callback_query.answer()
    state_data = await state.get_data()
    verif = state_data['verification']
    task_id = await db.add_task(state_data['task_title'], state_data['block_id'], state_data['verification'],
                                state_data['video_id'], state_data['abstract_id'], state_data['availability_files'],
                                state_data['deadline'])
    exercises = get_exersice()
    if verif == 'Ручная проверка':
        for exercise in exercises:
            exercise_condition = exercise[0]
            await db.add_exercise(task_id, exercise_condition)
    elif verif == 'Автоматическая проверка':
        for exercise in exercises:
            exercise_condition = exercise[0]
            exercise_answer = exercise[1]
            await db.add_exercise(task_id, exercise_condition, exercise_answer)

    users_by_course = await db.get_users_by_course(state_data['course_id'])
    for user_id in users_by_course:
        await bot.send_message(chat_id=user_id,
                               text=f'Привет! Только что был добавлен новый урок: {state_data['task_title']}\nЧтобы перейти к нему жми на кнопку!',
                               reply_markup=await kb.start_the_task_from_the_reminder(state_data['course_id'],
                                                                                task_id))
