from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router

import state as st
import keyboard as kb

router = Router()


@router.message(st.MappingExercise.solving_homework)
async def record_answer(message: Message, state: FSMContext):
    state_data = await state.get_data()
    quantity_exercise = state_data['quantity_exercise']
    current_exercise = state_data['current_exercise']
    condition, right_answer, exercise_id = state_data['homework'][current_exercise]
    message_id = state_data['current_message_id']
    input_answer = message.text
    result_answer = (right_answer == input_answer)
    status_input_answer = '✅' if result_answer else '❌'
    text_message = f'{condition}\nТвой ответ: {input_answer} {status_input_answer}'
    answers = state_data.get('results', {})
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
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text=text_message,
        reply_markup=await kb.mapping_homework(quantity_exercise, current_exercise)
    )
