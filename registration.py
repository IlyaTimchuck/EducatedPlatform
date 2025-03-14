from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import state as st
import database as db
import keyboard as kb
from handlers.command import command_menu

router = Router()


@router.message(st.Registration.get_name_user)
async def getting_name_user(message: Message, state: FSMContext):
    name_user = message.text
    await state.update_data(name_user=name_user)
    await message.answer(
        'Теперь отправь мне свою локацию или название ближайшего большого города. Это нужно для корректного отображения дедлайнов',
        reply_markup=kb.location_button)
    await state.set_state(st.Registration.get_location_user)


@router.message(st.Registration.get_location_user)
async def registration_user(message: Message, state: FSMContext):
    data = await state.get_data()
    latitude, longitude = None, None
    # Если пользователь отправил геолокацию, используем её
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
    # Если отправлен текст, считаем, что это название города и проводим геокодинг
    elif message.text:
        geolocator = Nominatim(user_agent="timezone_app")
        location = geolocator.geocode(message.text)
        if location is None:
            await message.answer("Город не найден. Пожалуйста, проверьте название и попробуйте еще раз.")
            return
        latitude = location.latitude
        longitude = location.longitude
    else:
        await message.answer("Пожалуйста, отправьте название города или свою геолокацию.")
        return

    # Определяем часовой пояс по координатам
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
    if timezone_name is None:
        await message.answer("Не удалось определить часовой пояс по указанным данным. Попробуйте снова.")
        return
    role = 'student' #if message.from_user.id != 795508218 else 'admin'
    # Регистрируем пользователя в базе данных
    result = await db.registration_user(data['name_user'], message.from_user.id, timezone_name, role)
    if result:
        text_message, keyboard = await kb.send_command_menu(message.from_user.id)
        message_menu_id = await message.answer(text_message, reply_markup=keyboard)
        if role == 'student':
            await state.set_state(st.MappingExercise.mapping_command_menu)
            await state.update_data(message_menu_id=message_menu_id)
    else:
        await message.answer(
            'Ты не был добавлен админом на курс, попробуй проверить введенные данные или обратиться к администратору :(')
        await state.clear()
        await state.set_state(st.Registration.get_name_user)
