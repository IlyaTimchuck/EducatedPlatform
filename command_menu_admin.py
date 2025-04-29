from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram import Router, F
from google_table import google_client
import database as db
import state as st
import keyboard as kb

router = Router()


@router.callback_query(lambda c: c.data.startswith('cancel_deleting') or c.data.startswith('confirm_deleting'))
async def process_deleting_user(callback_query: CallbackQuery):
    action, user_id = callback_query.data.split(':')
    user_id = int(user_id)
    if action == 'cancel_deleting':
        user_data = await db.get_data_user(user_id)
        course_title = await db.get_course_title(user_data['course_id'])
        timezone = (await db.get_timezones())[user_data['timezone_id']]
        user_data_for_table = [user_data['real_name'], user_data['telegram_username'], course_title, user_id, timezone,
                               user_data['date_of_joining'], 'student', 3]
        await google_client.add_user_in_table(*user_data_for_table)
        await callback_query.answer('Удаление было отменено. Все данные пользоателя восстановлены')
        await callback_query.message.delete()
    else:
        await db.delete_all_user_data(user_id)
        await callback_query.answer('Пользователь успешно удален')
        await callback_query.message.delete()

@router.callback_query(F.data == 'get_list_courses')
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.set_state(st.GetMetricsUser.getting_data)
    await callback_query.message.edit_text('Выбери курс:',
                                           reply_markup=await kb.choose_course_inline(for_add_task=False))


@router.callback_query(lambda c: c.data.startswith('course_selection_for_user_metrics'))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    course_id = int(callback_query.data.split(":")[-1])
    await state.update_data(course_id=course_id)
    await callback_query.message.edit_text('Выбери пользователя:',
                                           reply_markup=await kb.mapping_list_users(course_id))


@router.callback_query(lambda c: c.data.startswith('open_metric_user'))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = int(callback_query.data.split(":")[-1])
    await state.update_data(user_id=user_id, admin_connection=True)
    metrics_user = await db.get_metric_user(user_id)
    right_answers = metrics_user['right_answers']
    total_exercises = metrics_user['total_exercises']
    quotient = str(round((right_answers / total_exercises)) * 100) + '%' if total_exercises != 0 else '-'
    history_lives_user = await db.get_history_lives_user(callback_query.from_user.id)

    text_message = f'''Метрики пользователя📊
    
Всего задач решено: {right_answers}
Всего заданий на курсе: {total_exercises}
Процент выполнения: {quotient}

История жизней пользователя:\n'''
    for change in history_lives_user:
        action = change['action']
        if action == '-1':
            if change['task_title']:
                text_message += f'{action}❤️ Просрочен дедлайн к уроку {change['task_title']}\n'
            else:
                text_message += f'{action}❤️ Индивидуальное обновление жизней\n'
        elif action == '+3':
            text_message += f'{action}❤️ Новый блок!\n'
        else:
            text_message += f'{action}❤️ Индивидуальное обновление жизней\n'
    await callback_query.message.edit_text(text_message,
                                           reply_markup=await kb.get_more_metric(user_id))
