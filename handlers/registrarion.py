from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router

import state as st
import database as db
import keyboard as kb

router = Router()


@router.message(st.Registration.get_name)
async def confirm_registration(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    if await db.user_in_unregistered(data['username']):
        await db.registration_user(data['username'], message.from_user.id, 'student')
        await message.answer('Ты был успешно зарегестрирован на курсе, вот твоя панель управления',
                             reply_markup=kb.command_menu_student)
        await state.clear()
    elif message.from_user.id == 795508218:
        await message.answer('Сэр, Вы были распознаны как создатель этого бота, вот ваша палень админа',
                             reply_markup=kb.command_menu_admin)
    else:
        await message.answer(
            'Кажется, ты не был добавлен админом. Проверь правильность введенного имени или свяжись с админом :(')
