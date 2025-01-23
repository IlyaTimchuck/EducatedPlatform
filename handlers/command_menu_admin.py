from datetime import datetime

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router


import state as st
import database as db
import keyboard as kb
from database import current_datetime
from state import AddTask

router = Router()


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
    await db.add_users(list_users, data['course_tittle'])
    await message.answer('Пользователи были успешно добавлены', reply_markup=kb.command_menu_admin)


@router.message(st.AddTask.get_task_tittle)
async def process_get_task_tittle(message: Message, state: FSMContext):
    await state.update_data(task_tittle=message.text)
    await message.answer('Название было успешно записано. Теперь отправь мне видеозапись урока')
    await state.set_state(st.AddTask.get_video)


@router.message(st.AddTask.get_video)
async def process_get_video(message: Message, state: FSMContext):
    await state.update_data(video_id=message.video.file_id)
    await message.answer('Видео было успешно записано. Теперь отправь конспект урока')
    await state.set_state(st.AddTask.get_abstract)


@router.message(st.AddTask.get_abstract)
async def process_get_abstract(message: Message, state: FSMContext):
    year = datetime.now().year
    month = datetime.now().month
    await state.update_data(abstract_id=message.document.file_id)
    await message.answer('Выбери параметры домашней работы',
                         reply_markup=kb.generate_calendar(year, month))
    await state.set_state(st.AddTask.verification)


# @router.message(st.AddTask.verification)
# async def process_verification(message: Message, state: FSMContext):
#     await message.answer('Выбери параметры домашней работы',
#                          reply_markup=kb.choose_parameters_task('Автоматическая проверка', datetime.now()))
#     await state.set_state(AddTask.get_homework)


# @router.message(st.AddTask.get_homework)
# async def process_get_homework(message: Message, state: FSMContext):
#     state_data = await state.get_data()
#     await db.add_task(state_data['task_tittle'], state_data['selected_block'])
#     task_id = await db.get_task_id()
#     if state_data['manual_verification']:
#         condition = message.text
#         await db.add_exercise(state_data[])
#
#     data = message.text.split('ОТВЕТ')
#     condition = data[0]
#     answer = data[-1].lstrip()
#     await db.add_exercise(state_data['task_id'], state_data['exercise_number'], condition, answer)
