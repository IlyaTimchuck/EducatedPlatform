from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router

import state as st
import database as db
import keyboard as kb

router = Router()


@router.message(st.Registration.get_info_user)
async def confirm_registration(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    if await db.user_is_unregistered(data['username']):
        await message.answer(
            'Теперь отправь мне свое местоположение или введи название ближайшего большого города. Это нужно для правильного отображения дедлайнов',
            reply_markup=kb.location_button)
        await state.set_state(st.Registration.registration_user)
    else:
        await message.answer(
            'Кажется, ты не был добавлен админом. Проверь правильность введенного имени или свяжись с админом :(')


@router.message(st.Registration.registration_user)
async def registration_user(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text:
        pass
    elif message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
    # if message.from_user.id == 795508218:
    #     await db.registration_user(data['username'], message.from_user.id, 'admin')
    #     await message.answer('Сэр, Вы были распознаны как создатель этого бота, вот ваша палень админа',
    #                          reply_markup=kb.command_menu_admin)
    #     await state.clear()
    # else:
    #     await db.registration_user(data['username'], message.from_user.id, 'student')
