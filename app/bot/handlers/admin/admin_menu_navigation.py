from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram import Router, F

import app.bot.infrastructure.database as db
import app.bot.states.state as st
import app.bot.keyboards as kb

router = Router()


@router.callback_query(F.data == 'get_list_courses')
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.set_state(st.GetMetricsUser.getting_data)
    await callback_query.message.edit_text('Выбери курс:',
                                           reply_markup=await kb.admin_keyboards.create_task_keyboards.choose_course_inline(
                                               for_add_task=False))


@router.callback_query(lambda c: c.data.startswith('course_selection_for_user_metrics'))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    if state_data.get('user_id'):
        state_data.pop('user_id')
        await state.set_data(state_data)
    course_id = int(callback_query.data.split(":")[-1])
    await state.update_data(course_id=course_id)
    await callback_query.message.edit_text('Выбери пользователя:',
                                           reply_markup=await kb.admin_keyboards.manage_students.mapping_list_users(
                                               course_id))


@router.callback_query(lambda c: c.data.startswith('open_metric_user'))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = int(callback_query.data.split(":")[-1])
    course_id = await state.get_value('course_id')
    await state.update_data(user_id=user_id, admin_connection=True)
    metrics_user = await db.metrics.get_metric_user(user_id)
    right_answers = metrics_user['right_answers']
    total_exercises = metrics_user['total_exercises']
    quotient = str(round((right_answers / total_exercises)) * 100) + '%' if total_exercises != 0 else '-'
    history_lives_user = await db.metrics.get_history_lives_user(callback_query.from_user.id)

    text_message = f'''Метрики пользователя📊
    
Всего задач решено: {right_answers}
Всего заданий на курсе: {total_exercises}
Процент выполнения: {quotient}

История жизней пользователя:\n'''
    for change in history_lives_user:
        action = change['action']
        if action == '-1':
            if change['task_title']:
                text_message += f"{action}❤️ Просрочен дедлайн к уроку {change['task_title']}\n"
            else:
                text_message += f"{action}❤️ Индивидуальное обновление жизней\n"
        elif action == '+3':
            text_message += f"{action}❤️ Новый блок!\n"
        else:
            text_message += f"{action}❤️ Индивидуальное обновление жизней\n"
    await callback_query.message.edit_text(text_message,
                                           reply_markup=await kb.admin_keyboards.manage_students.get_more_metric(course_id))
