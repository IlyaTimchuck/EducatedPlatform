from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram import Router, F

import calendar
import state as st
import database as db
import keyboard as kb

router = Router()


@router.callback_query(lambda call: call.data in ['back_student', 'back_admin'])
async def process_back_button(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    if callback_query.data == 'back_student':
        await callback_query.message.edit_text('Вот твое командное меню', reply_markup=kb.command_menu_student)
    elif callback_query.data == 'back_admin':
        await callback_query.message.edit_text('Вот твое командное меню', reply_markup=kb.command_menu_admin)
    await state.clear()


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


@router.callback_query(
    lambda c: c.data.startswith("increase_block") or c.data.startswith("reduce_block") or c.data.startswith(
        "confirm_block"))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    action, current_value = callback_query.data.split(":")
    current_block = int(current_value)
    if action == "increase_block":
        current_block += 1
    elif action == "reduce_block" and current_block != 1:
        current_block -= 1
    elif action == 'confirm_block':
        await callback_query.message.edit_text(text='Блок выбран. Теперь отправь мне название урока',
                                               reply_markup=kb.back_button_admin)
        state_data = await state.get_data()
        block_id = await db.add_block(state_data['course_tittle'], current_block)
        await state.update_data(block_id=block_id)
        await state.set_state(st.AddTask.get_task_tittle)
    new_text = f'Выбери блок\n\nТекущий выбор: {current_block}'
    if callback_query.message.text != new_text:
        await callback_query.message.edit_text(text=f'Выбери блок\n\nТекущий выбор: {current_block}',
                                           reply_markup=kb.to_change_block(current_block))


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
    new_markup = kb.generate_calendar(year, month)
    await callback_query.message.edit_reply_markup(reply_markup=new_markup)


@router.callback_query(lambda c: c.data.startswith("select_day"))
async def select_day(callback_query: CallbackQuery):
    _, year, month, day = callback_query.data.split(":")
    await callback_query.message.edit_text(
        f"Дата дедлайна: {day} {calendar.month_name[int(month)]} {year}\nВыбери тип проверки:",
        reply_markup=kb.choose_parameters_task(f'{day}-{month}-{year}'))


@router.callback_query((lambda c: c.data.startswith('verif')))
async def choose_verification(callback_query: CallbackQuery):
    await callback_query.answer()
    _, verif, deadline_date = callback_query.data.split(':')
    verif = 'Автоматическая проверка' if verif == 'auto' else 'Ручная проверка'
    year, month, day = deadline_date.split('-')
    await callback_query.message.edit_text(
        f'''Дата дедлайна: {day} {calendar.month_name[int(month)]} {year}\nТип проверки: {verif}''')


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback_query: CallbackQuery):
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith('choose_course'))
async def process_increase_block(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    course_name = callback_query.data.split(":")[-1]
    current_block = await db.get_block(course_name, current=True)
    await state.update_data(course_tittle=course_name)
    await state.set_state(st.AddTask.choose_course)
    await callback_query.message.edit_text(f'Выбери блок\n\nТекущий выбор: {current_block}',
                                           reply_markup=kb.to_change_block(current_block))


@router.callback_query(F.data == 'send_homework')
async def process_send_homework(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = state.get_data()
    print(data)
    await state.set_state(...)
