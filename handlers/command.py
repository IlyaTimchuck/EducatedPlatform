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
    await state.set_state(st.Registration.get_name_user)

@router.message(Command(commands=['command_menu']))
async def command_menu(message: types.Message):
    text_message, keyboard = await kb.send_command_menu(message.from_user.id)
    await message.answer(text_message, reply_markup=keyboard)