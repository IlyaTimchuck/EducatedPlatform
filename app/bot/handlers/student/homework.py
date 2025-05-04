from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaVideo, Message
from aiogram import Router, F
from datetime import datetime

from app.bot.bot_instance import bot
import app.bot.states.state as st

import app.bot.infrastructure.database as db
import app.bot.keyboards.command_menu_student as kb

router = Router()


@router.callback_query(lambda c: c.data.startswith('next_exercise') or c.data.startswith('prev_exercise')
                                 or c.data.startswith('open_exercise'))
async def mapping_exercise(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    current_exercise = int(callback_query.data.split(':')[-1])
    state_data = await state.get_data()
    admin_connection = state_data.get('admin_connection')
    quantity_exercise = state_data['quantity_exercise']
    homework = state_data['homework']
    answers = state_data.get('results', {})
    file_work = state_data['task_data'].get('file_work')
    if current_exercise in answers:
        answer_data = answers[current_exercise]
        user_answer = answer_data.get('input_answer', '')
        status = answer_data.get('status_input_answer', '')
        text_message = f"{homework[current_exercise][0]}\nТвой ответ: {user_answer} {status}"
    else:
        text_message = homework[current_exercise][0]

    current_message = await callback_query.message.edit_text(
        text=text_message,
        reply_markup=await kb.mapping_homework(quantity_exercise, current_exercise, file_work, admin_connection)
    )

    await state.update_data(
        current_exercise=current_exercise,
        current_text=current_message.text,
        current_message_id=current_message.message_id)


@router.message(st.MappingExercise.solving_homework)
async def record_answer(message: Message, state: FSMContext):
    state_data = await state.get_data()
    quantity_exercise = state_data['quantity_exercise']
    current_exercise = state_data['current_exercise']
    condition, right_answer, exercise_id = state_data['homework'][current_exercise]
    message_id = state_data['homework_message_id']
    input_answer = message.text
    result_answer = (right_answer == input_answer)
    status_input_answer = '✅' if result_answer else '❌'
    text_message = f'{condition}\nТвой ответ: {input_answer} {status_input_answer}'
    answers = state_data.get('results', {})
    file_work = state_data['task_data'].get('file_work')
    prev_status = answers.get(current_exercise, {}).get('status_input_answer')
    quantity_right_answers = state_data.get('quantity_right_answers', 0)
    if prev_status is None:
        if result_answer:
            quantity_right_answers += 1
    else:
        if prev_status == '❌' and result_answer:
            quantity_right_answers += 1
        elif prev_status == '✅' and not result_answer:
            quantity_right_answers -= 1
    answers[current_exercise] = {'input_answer': input_answer, 'status_input_answer': status_input_answer}
    await state.update_data(results=answers, quantity_right_answers=quantity_right_answers)
    await message.delete()
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text_message,
            reply_markup=await kb.mapping_homework(quantity_exercise, current_exercise, bool(file_work))
        )
    except TelegramBadRequest:
        pass


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
        file_work_id = message.document.file_id
        user_progress = ''
        for exercise_num in range(1, len(state_data.get('homework')) + 1):
            solve_user = state_data['results'].get(exercise_num)
            if solve_user:
                user_progress += f"{exercise_num}) {solve_user['input_answer']}{solve_user['status_input_answer']}\n"
            else:
                user_progress += f"{exercise_num}) Ответ не был дан❌\n"
        await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=state_data['homework_message_id'],
                                            reply_markup=None)
        sent_message = await message.answer(
            text=f'Файл успешно загружен\nТвои ответы:\n{user_progress}\nОтправить все и завершить домашнюю работу?',
            reply_markup=kb.confirm_completing_work_file)
        messages_getting_file_work += [message_user_id, sent_message.message_id]
        await state.update_data(file_work_id=file_work_id, messages_getting_file_work=messages_getting_file_work)
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
    file_work_id = state_data.get('file_work_id')
    message_file_work_id = state_data.get('message_file_work_id')
    file_work_info = {'file_work': bool(file_work_id), 'file_work_retrieved': bool(message_file_work_id)}
    if messages_getting_file_work:
        # удаляем homework_message + сообщения от заверешения homework
        for message_id in messages_getting_file_work:
            await bot.delete_message(chat_id=callback_query.from_user.id, message_id=message_id)
        state_data.pop('messages_getting_file_work')
    else:
        # удаляем только homework_message
        await callback_query.message.delete()
    state_data.pop('homework_message_id')
    session_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quotient = int((state_data.get('quantity_right_answers', 0) / state_data['quantity_exercise']) * 100)
    is_completed = quotient >= 90
    await db.sessions.add_progress_user(callback_query.from_user.id, task_data['task_id'], state_data['homework'],
                               state_data.get('results', {}), state_data['session_start'], session_end, file_work_id,
                               is_completed)
    await state.update_data(session_end=session_end)
    state_data['session_end'] = session_end
    await callback_query.answer(
        'Домашняя работа была принята' if is_completed else 'Порог не был пройден. Нужно минимум 90%',
        show_alert=False if is_completed else True)
    text_message = f'Название урока: {task_data['task_title']}\nДедлайн: {task_data['deadline']}\nДомашняя работа: {quotient}% {'✅' if quotient >= 90 else '❌'}'
    link_files = task_data.get('link_files', None)
    if link_files:
        text_message += f'\n\nФайлы к домашней работе: {link_files}'
    message_abstract_id = state_data.get('message_abstract_id', False)
    await state.set_data(state_data)
    await callback_query.bot.edit_message_media(
        chat_id=callback_query.message.chat.id,
        message_id=state_data['task_message_id'],
        media=InputMediaVideo(
            media=task_data['video_id'],
            caption=text_message),
        reply_markup=await kb.mapping_task(task_data['block_id'], file_work_info,
                                           bool(message_abstract_id))
    )


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback_query: CallbackQuery):
    await callback_query.answer()
