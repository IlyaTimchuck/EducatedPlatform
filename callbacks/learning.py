from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaVideo, InlineKeyboardMarkup, Message
from aiogram import Router, F
from datetime import datetime

from bot_instance import bot
import state as st
import database as db
import keyboard as kb

router = Router()


@router.callback_query(F.data == 'block_list')
async def open_blocks_list(callback_query: CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    user_data = await db.get_data_user(user_id)
    await callback_query.message.edit_text('🎓 Доступные блоки занятий:',
                                           reply_markup=await kb.mapping_block_list(user_data['course_id']))


@router.callback_query(lambda c: c.data.startswith('open_block'))
async def open_tasks_list(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    action, course_id, block_id = callback_query.data.split(':')
    user_id = callback_query.from_user.id
    if action == 'open_block_from_homework':
        state_data = await state.get_data()
        abstract = state_data.get('message_abstract_id', False)
        if abstract:
            await callback_query.message.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=abstract)
            state_data.pop('message_abstract_id')
        await callback_query.message.delete()
        command_menu = await callback_query.message.answer('Список занятий:',
                                                           reply_markup=await kb.mapping_list_tasks(user_id,
                                                                                                    int(course_id),
                                                                                                    int(block_id)))
        await state.clear()
        await state.set_state(st.MappingExercise.mapping_task)
        await state.update_data(course_id=course_id, command_menu_id=command_menu.message_id)

    else:
        await state.update_data(course_id=course_id)
        await callback_query.message.edit_text('Список занятий:',
                                               reply_markup=await kb.mapping_list_tasks(user_id, int(course_id),
                                                                                        int(block_id)))


@router.callback_query(lambda c: c.data.startswith('open_task'))
async def open_task(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.set_state(st.MappingExercise.mapping_task)
    state_data = await state.get_data()
    action, course_id, task_id, from_remind = callback_query.data.split(':')
    if int(from_remind):
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=state_data['command_menu_id'])
    task_id = int(task_id)
    task_data = await db.get_data_task(task_id)
    date_obj = datetime.strptime(task_data['deadline'], '%Y-%m-%d')
    deadline = date_obj.strftime('%d-%m-%Y')
    text_message = f'Название урока: {task_data['task_title']}\nДедлайн: {deadline}'
    session = await db.get_last_session(callback_query.from_user.id, task_id)
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
        reply_markup=await kb.mapping_task(course_id, task_data['block_id'],
                                           message_abstract_id)
    )
    await state.update_data(task_data=task_data, task_message_id=sent_message.message_id, course_id=course_id,
                            file_work=bool(file_work))


@router.callback_query(F.data == 'open_homework')
async def mapping_homework(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.edit_reply_markup(reply_markup=None)
    state_data = await state.get_data()
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
                                                                                                  file_work))
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


@router.callback_query(F.data == 'get_abstract')
async def send_abstract(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    task_data = (await state.get_data())['task_data']
    sent_message = await callback_query.message.answer_document(document=task_data['abstract_id'])
    await state.update_data(message_abstract_id=sent_message.message_id)
    current_keyboard = callback_query.message.reply_markup.inline_keyboard
    new_keyboard = [
        [button for button in row if button.callback_data != 'get_abstract']
        for row in current_keyboard
    ]
    await callback_query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=new_keyboard)
    )


@router.callback_query(lambda c: c.data.startswith('next_exercise') or c.data.startswith('prev_exercise')
                                 or c.data.startswith('open_exercise'))
async def mapping_exercise(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    current_exercise = int(callback_query.data.split(':')[-1])
    state_data = await state.get_data()
    quantity_exercise = state_data['quantity_exercise']
    homework = state_data['homework']
    answers = state_data.get('results', {})
    file_work = state_data.get('file_work')
    if current_exercise in answers:
        answer_data = answers[current_exercise]
        user_answer = answer_data.get('input_answer', '')
        status = answer_data.get('status_input_answer', '')
        text_message = f"{homework[current_exercise][0]}\nТвой ответ: {user_answer} {status}"
    else:
        text_message = homework[current_exercise][0]

    current_message = await callback_query.message.edit_text(
        text=text_message,
        reply_markup=await kb.mapping_homework(quantity_exercise, current_exercise, file_work)
    )

    await state.update_data(
        current_exercise=current_exercise,
        current_text=current_message.text,
        current_message_id=current_message.message_id)


@router.callback_query(F.data == 'get_file_work')
async def getting_file_work(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    homework_message_id = state_data.get('homework_message_id')
    await bot.edit_message_text(
        text='Твои ответы были сохранены. \nТеперь отправь рабочий файл с решениями',
        reply_markup=kb.back_to_homework,
        chat_id=callback_query.from_user.id, message_id=homework_message_id)
    await state.update_data(messages_getting_file_work=[homework_message_id])
    await state.set_state(st.MappingExercise.getting_work_file)


@router.message(st.MappingExercise.getting_work_file)
async def getting_work_file(message: Message, state: FSMContext):
    state_data = await state.get_data()
    messages_getting_file_work = state_data.get('messages_getting_file_work', [])
    try:
        message_user_id = message.message_id
        file_work = message.document.file_id
        user_progress = ''
        for exercise_num in range(1, len(state_data.get('homework')) + 1):
            solve_user = state_data['results'].get(exercise_num)
            if solve_user:
                user_progress += f"{exercise_num}) {solve_user['input_answer']}{solve_user['status_input_answer']}\n"
            else:
                user_progress += f"{exercise_num}) Ответ не был дан❌\n"
        await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=state_data['homework_message_id'], reply_markup=None)
        sent_message = await message.answer(text=f'Файл успешно загружен\nТвои ответы:\n{user_progress}\nОтправить все и завершить домашнюю работу?', reply_markup=kb.confirm_completing_work_file)
        messages_getting_file_work += [message_user_id, sent_message.message_id]
        await state.update_data(file_work=file_work, messages_getting_file_work=messages_getting_file_work)
    except Exception as e:
        print(e)
        sent_message = await message.answer(
            'Ошибка чтения файла. Проверь, правильный ли формат файла ты используешь. Отправь мне файл повторно')
        messages_getting_file_work += [sent_message.message_id]
        await state.set_state(st.MappingExercise.getting_work_file)


@router.callback_query(F.data == 'complete_homework')
async def completing_homework(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    task_data = state_data['task_data']
    messages_getting_file_work = state_data.get('messages_getting_file_work')
    if messages_getting_file_work:
        for message_id in messages_getting_file_work:
            await bot.delete_message(chat_id=callback_query.from_user.id, message_id=message_id)
        await state.update_data(messages_getting_file_work=[])
    else:
        await callback_query.message.delete()
    session_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quotient = int((state_data.get('quantity_right_answers', 0) / state_data['quantity_exercise']) * 100)
    is_completed = quotient >= 90
    await db.add_progress_user(callback_query.from_user.id, task_data['task_id'], state_data['homework'],
                               state_data.get('results', {}), state_data['session_start'], session_end, is_completed)
    await state.update_data(session_end=session_end)
    await callback_query.answer(
        'Домашняя работа была принята' if is_completed else 'Порог не был пройден. Нужно минимум 90%',
        show_alert=False if is_completed else True)
    text_message = f'Название урока: {task_data['task_title']}\nДедлайн: {task_data['deadline']}\nДомашняя работа: {quotient}% {'✅' if quotient >= 90 else '❌'}'
    link_files = task_data.get('link_files', None)
    if link_files:
        text_message += f'\n\nФайлы к домашней работе: {link_files}'
    message_abstract_id = state_data.get('message_abstract_id', False)
    await callback_query.bot.edit_message_media(
        chat_id=callback_query.message.chat.id,
        message_id=state_data['task_message_id'],
        media=InputMediaVideo(
            media=task_data['video_id'],
            caption=text_message),
        reply_markup=await kb.mapping_task(state_data['course_id'], task_data['block_id'],
                                            bool(message_abstract_id))
    )


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback_query: CallbackQuery):
    await callback_query.answer()
