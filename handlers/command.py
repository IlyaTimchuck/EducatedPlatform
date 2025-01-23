from aiogram.filters import Command
from aiogram import Router, types
from aiogram.fsm.context import FSMContext

import state as st
import database as db
import keyboard as kb

router = Router()

@router.message(Command(commands=['start']))
async def start(message: types.Message, state: FSMContext):
    await message.answer('Привет! Чтобы начать обучение отправь мне свои ФИО')
    await state.set_state(st.Registration.get_name)

@router.message(Command(commands=['command_menu']))
async def command_menu(message: types.Message):
    user_data = await db.get_data_user(message.from_user.id)
    if user_data['role'] == 'student':
        await message.answer('Это твоё командное меню', reply_markup=kb.command_menu_student)
    elif user_data['role'] == 'admin':
        await message.answer('Это твое командное меню', reply_markup=kb.command_menu_admin)