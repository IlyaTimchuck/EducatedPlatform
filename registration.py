from datetime import datetime

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import state as st
import database as db
import keyboard as kb
import utils
from google_table import google_client

router = Router()


@router.message(st.Registration.get_name_user)
async def getting_name_user(message: Message, state: FSMContext):
    name_user_split = message.text.split()
    reg_msg_for_deletion = await state.get_value('reg_msg_for_deletion', [])
    if len(name_user_split) == 2 and len(name_user_split[0]) >= 2 and len(name_user_split[1]) >= 2:
        name_user = f'{name_user_split[0][0].upper()}{name_user_split[0][1:].lower()} {name_user_split[1][0].upper()}{name_user_split[1][1:].lower()}'
        sent_message = await message.answer(
            'Теперь отправь мне свою локацию или название ближайшего большого города. Это нужно для корректного отображения дедлайнов',
            reply_markup=kb.location_button)
        reg_msg_for_deletion += [sent_message.message_id]
        reg_msg_for_deletion += [message.message_id]
        await state.update_data(real_name=name_user, reg_msg_for_deletion=reg_msg_for_deletion)
        await state.set_state(st.Registration.get_location_user)
    else:
        sent_message = await message.answer('Кажется, ты отправил некорректные имя/фамилию. Попробуй еще раз')
        reg_msg_for_deletion += [sent_message.message_id]
        reg_msg_for_deletion += [message.message_id]
        await state.update_data(reg_msg_for_deletion=reg_msg_for_deletion)
        await state.set_state(st.Registration.get_name_user)


@router.message(st.Registration.get_location_user)
async def registration_user(message: Message, state: FSMContext):
    state_data = await state.get_data()
    reg_msg_for_deletion = state_data['reg_msg_for_deletion']
    reg_msg_for_deletion += [message.message_id]
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
            sent_message_1 = await message.answer(
                "Город не найден. Пожалуйста, проверьте название и попробуйте еще раз.")
            reg_msg_for_deletion += [sent_message_1.message_id]
            return
        latitude = location.latitude
        longitude = location.longitude
    else:
        await message.answer("Пожалуйста, отправь название города или свою геолокацию.")
        return

    # Определяем часовой пояс по координатам
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
    if timezone_name is None:
        sent_message_2 = await message.answer(
            "Не удалось определить часовой пояс по указанным данным. Попробуйте снова.")
        reg_msg_for_deletion += [sent_message_2.message_id]
        return
    role = 'student' if message.from_user.id != 795508218 else 'admin'
    real_name_user = state_data['real_name']
    # Регистрируем пользователя в базе данных
    course_user = await db.registration_user(real_name_user, message.from_user.username, message.from_user.id,
                                             timezone_name, role)
    if course_user:
        date_of_joining = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_message, keyboard = await kb.send_command_menu(message.from_user.id)
        text_message = f'Твой часовой пояс распознан как {timezone_name}\n' + text_message
        await utils.del_messages(message.from_user.id, reg_msg_for_deletion)
        message_menu = await message.answer(text_message, reply_markup=keyboard)
        await google_client.add_user_in_table(real_name_user, message.from_user.username, course_user[1],
                                              message.from_user.id,
                                              timezone_name, date_of_joining, role, 3)
        state_data['command_menu_id'] = message_menu.message_id
        state_data.pop('reg_msg_for_deletion')
        if role == 'student':
            await state.set_state(st.MappingExercise.mapping_command_menu)
            await state.set_data(state_data)
    else:
        sent_message_3 = await message.answer(
            'Ты не был добавлен админом на курс. Тебе нужно обратиться к админу :(')
        reg_msg_for_deletion += [sent_message_3.message_id]
        await state.set_state(st.Registration.get_location_user)
