from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram import Router, F

import app.bot.states.state as st
import app.bot.infrastructure.database as db
import app.bot.keyboards as kb
from app.bot.infrastructure.api.google_table import google_client

router = Router()


@router.callback_query(F.data == 'add_users')
async def process_add_users(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer('Выбери курс',
                                        reply_markup=await kb.admin_keyboards.manage_students.choose_course_reply())
    await state.set_state(st.AddUsers.choose_course)


@router.message(st.AddUsers.choose_course)
async def process_choose_course(message: Message, state: FSMContext):
    if message.text == 'Создать новый':
        await message.answer('Отправь мне название курса')
        await state.set_state(st.AddUsers.get_course_tittle)
    else:
        await state.update_data(course_title=message.text)
        await message.answer('Отправь мне список пользователей')
        await state.set_state(st.AddUsers.get_list_users)


@router.message(st.AddUsers.get_course_tittle)
async def process_get_course_tittle(message: Message, state: FSMContext):
    course_name = message.text
    await state.update_data(course_title=course_name)
    course_id = await db.courses.create_course(message.text)
    await google_client.add_course_in_table([course_name, course_id])
    await message.answer('Отправь мне список пользователей')
    await state.set_state(st.AddUsers.get_list_users)


@router.message(st.AddUsers.get_list_users)
async def process_get_list_users(message: Message, state: FSMContext):
    list_users = message.text.split('\n')
    data = await state.get_data()
    course_id = await db.courses.get_course_id(data['course_title'])
    await db.users.add_users(list_users, course_id)
    _, keyboard = await kb.main_menu.send_command_menu(message.from_user.id)
    await message.answer('Пользователи были успешно добавлены', reply_markup=keyboard)
