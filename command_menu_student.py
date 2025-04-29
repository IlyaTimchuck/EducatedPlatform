from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from bot_instance import bot
from aiogram.types import CallbackQuery, InputMediaVideo
import state as st
import database as db
import keyboard as kb

router = Router()


@router.callback_query(F.data == 'list_lives')
async def opening_list_lives(callback_query: CallbackQuery):
    await callback_query.answer()
    history_lives_user = await db.get_history_lives_user(callback_query.from_user.id)
    text_message = "📝 История изменений жизней:\n\n"
    for change in history_lives_user:
        action = change['action']
        if action == '-1':
            if change['task_title']:
                text_message += f'{action}❤️ Просрочен дедлайн {change['task_title']}\n'
            else:
                text_message += f'{action}❤️ Индивидуальное обновление жизней\n'
        elif action == '+3':
            text_message += f'{action}❤️ Новый блок!\n'
        else:
            text_message += f'{action}❤️ Индивидуальное обновление жизней\n'
    await callback_query.message.edit_text(text=text_message, reply_markup=kb.back_button_admin)


@router.callback_query(lambda c: c.data.startswith('block_list'))
async def open_blocks_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    admin_connection = state_data.get('admin_connection')
    user_id = state_data['user_id'] if admin_connection else callback_query.from_user.id
    state_data['user_id'] = user_id
    user_data = await db.get_data_user(user_id)
    course_id = user_data['course_id']
    state_data['course_id'] = course_id
    reminder_message_id = state_data.get('reminder_message_id')
    notification_about_new_task_message_id = state_data.get('notification_about_new_task_message_id')

    if reminder_message_id:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=reminder_message_id)
        state_data.pop('reminder_message_id')
    if notification_about_new_task_message_id:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=notification_about_new_task_message_id)
        state_data.pop('notification_about_new_task_message_id')

    await callback_query.message.edit_text('🎓 Доступные блоки занятий:',
                                           reply_markup=await kb.mapping_block_list(user_id, course_id,
                                                                                    admin_connection=admin_connection))
    await state.set_data(state_data)


@router.callback_query(lambda c: c.data.startswith('open_block'))
async def open_tasks_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    callback_data_split = callback_query.data.split(':')
    if len(callback_data_split) == 2:
        action, block_id = callback_query.data.split(':')
    else:
        action = callback_query.data
        block_id = state_data['block_id']

    course_id = state_data['course_id']
    user_id = state_data.get('user_id', callback_query.from_user.id)

    admin_connection = state_data.get('admin_connection', False)

    if action == 'open_block_from_homework':
        command_menu_id = state_data['command_menu_id']
        abstract_message = state_data.get('message_abstract_id')
        homework_message = state_data.get('homework_message_id')
        if abstract_message:
            await callback_query.message.bot.delete_message(chat_id=callback_query.from_user.id,
                                                            message_id=abstract_message)
        if homework_message:
            await callback_query.message.bot.delete_message(chat_id=callback_query.from_user.id,
                                                            message_id=homework_message)
        await callback_query.message.bot.delete_message(chat_id=callback_query.from_user.id, message_id=command_menu_id)
        command_menu = await callback_query.message.answer('Список занятий:',
                                                           reply_markup=await kb.mapping_list_tasks(user_id,
                                                                                                    int(course_id),
                                                                                                    int(block_id)))
        await state.clear()
        await state.set_state(st.MappingExercise.mapping_task)
        data = {
            "user_id": user_id,
            "course_id": course_id,
            "command_menu_id": command_menu.message_id,
            "block_id": block_id,
        }

        if admin_connection:
            data["admin_connection"] = admin_connection

        await state.update_data(**data)

    else:
        await state.update_data(course_id=course_id, block_id=block_id)
        await callback_query.message.edit_text('Список занятий:',
                                               reply_markup=await kb.mapping_list_tasks(user_id, int(course_id),
                                                                                        int(block_id)))


@router.callback_query(lambda c: c.data.startswith('open_task'))
async def open_task(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.set_state(st.MappingExercise.mapping_task)
    state_data = await state.get_data()
    user_id = state_data.get('user_id', callback_query.from_user.id)
    if callback_query.data == 'open_task':
        last_task = await db.get_last_task(user_id)
        course_id, block_id, task_id = last_task.values()
        await state.update_data(course_id=course_id, block_id=block_id, task_id=task_id)
    else:
        _, course_id, task_id, from_remind = callback_query.data.split(':')
        if int(from_remind):
            await bot.delete_message(chat_id=callback_query.from_user.id, message_id=state_data['command_menu_id'])
            state_data.pop('command_menu_id')
            await state.set_data(state_data)
    task_id = int(task_id)
    task_data = await db.get_data_task(task_id)
    date_obj = datetime.strptime(task_data['deadline'], '%Y-%m-%d')
    deadline = date_obj.strftime('%d-%m-%Y')
    text_message = f'Название урока: {task_data['task_title']}\nДедлайн: {deadline}'
    session = await db.get_last_session(user_id, task_id)
    progress_user = await db.get_progress_user(task_id, session['session_id']) if session else \
        await db.get_progress_user(task_id)
    if progress_user:
        await state.update_data(results=progress_user)
        right_answers = len(
            [exercise_num for exercise_num in progress_user if
             progress_user[exercise_num]['status_input_answer'] == '✅'])
        quantity_exercise = len(await db.get_list_exercises(task_data['task_id']))
        quotient = int((right_answers / quantity_exercise) * 100)
        text_message += f"\nДомашняя работа: {quotient}% {'✅' if quotient >= 90 else '❌'}"
        await state.update_data(quantity_right_answers=right_answers, quantity_exercise=quantity_exercise)
    file_work = task_data.get('file_work', None)
    link_files = task_data.get('link_files', None)
    if file_work:
        text_message += '\n❗Чтобы завершить эту домшнюю работу, нужно будет отправить файл с решениями'
    if link_files:
        text_message += f'\n\nФайлы к домашней работе: {link_files}'
    message_abstract_id = state_data.get('message_abstract_id', False)
    sent_message = await callback_query.message.edit_media(
        media=InputMediaVideo(
            media=task_data['video_id'],
            caption=text_message),
        reply_markup=await kb.mapping_task(task_data['block_id'],
                                           message_abstract_id)
    )
    await state.update_data(task_data=task_data, task_message_id=sent_message.message_id, course_id=course_id,
                            file_work=bool(file_work))


@router.callback_query(F.data == 'open_homework')
async def mapping_homework(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.edit_reply_markup(reply_markup=None)
    state_data = await state.get_data()
    admin_connection = state_data.get('admin_connection', False)
    file_work = state_data.get('file_work')
    homework = await db.get_list_exercises(state_data['task_data']['task_id'])
    await state.set_state(st.MappingExercise.solving_homework)
    messages_getting_file_work = state_data.get('messages_getting_file_work')
    if messages_getting_file_work:
        for message_id in messages_getting_file_work:
            await bot.delete_message(chat_id=callback_query.from_user.id, message_id=message_id)
        state_data.pop('messages_getting_file_work')
        await state.set_data(state_data)
    quantity_exercise = len(homework)
    current_exercise = 1
    if 'results' in state_data:
        text_message = f'{homework[current_exercise][0]}\nТвой ответ: {' '.join(map(str, state_data['results'].get(current_exercise, {}).values()))}'
    else:
        text_message = homework[current_exercise][0]
    homework_message = await callback_query.message.answer(text=text_message,
                                                           reply_markup=await kb.mapping_homework(quantity_exercise,
                                                                                                  current_exercise,
                                                                                                  file_work,
                                                                                                  admin_connection))
    await state.update_data(quantity_exercise=quantity_exercise, homework=homework, current_exercise=current_exercise,
                            homework_message_id=homework_message.message_id,
                            session_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@router.callback_query(F.data == 'open_list_exercises')
async def opening_list_exercises(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    await callback_query.message.edit_text(text='Выбери задание',
                                           reply_markup=await kb.mapping_list_exercises(state_data,
                                                                                        'results' in state_data))
