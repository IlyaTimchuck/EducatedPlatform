from datetime import datetime

from aiogram.filters import Command
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot_instance import bot
import state as st
import database as db
import keyboard as kb
from callbacks.learning import completing_homework

router = Router()


@router.message(Command(commands=['start']))
async def start(message: types.Message, state: FSMContext):
    sent_message = await message.answer('Привет! Чтобы начать обучение отправь мне свои ФИО')
    message_user = message.message_id
    await state.set_state(st.Registration.get_name_user)
    await state.update_data(reg_msg_for_deletion=[sent_message.message_id, message_user])


@router.message(Command(commands=['command_menu']))
async def command_menu(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    message_menu_id = state_data.get('command_menu_id', None)
    message_abstract_id = state_data.get('message_abstract_id', None)
    session_start = state_data.get('session_start', None)
    session_end = state_data.get('session_end', None)
    reminder_message_id = state_data.get('reminder_message_id', None)
    notification_about_new_task_message_id = state_data.get('notification_about_new_task_message_id', None)
    messages_getting_file_work = state_data.get('messages_getting_file_work')
    if message_menu_id:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_menu_id)
    if message_abstract_id:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_abstract_id)
    if reminder_message_id:
        await bot.delete_message(chat_id=message.from_user.id, message_id=reminder_message_id)
    if notification_about_new_task_message_id:
        await bot.delete_message(chat_id=message.from_user.id, message_id=notification_about_new_task_message_id)
    if messages_getting_file_work:
        for message_id in messages_getting_file_work:
            await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
    elif session_start and not session_end:
        await bot.delete_message(chat_id=message.from_user.id, message_id=state_data['homework_message_id'])

    text_message, keyboard = await kb.send_command_menu(message.from_user.id)
    new_command_menu_id = await message.answer(text_message, reply_markup=keyboard)
    await state.clear()
    await state.set_state(st.MappingExercise.mapping_command_menu)
    await state.update_data(command_menu_id=new_command_menu_id.message_id)


@router.callback_query(lambda call: call.data in ['back_student', 'back_admin'])
async def process_back_button(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    text_message, keyboard = await kb.send_command_menu(callback_query.from_user.id)
    state_data = await state.get_data()
    abstract = state_data.get('message_abstract_id')
    if abstract:
        await callback_query.message.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=abstract)
        state_data.pop('message_abstract_id')
        await state.set_data(state_data)
    try:
        await callback_query.message.edit_text(
            text=text_message,
            reply_markup=keyboard
        )
        return
    except TelegramBadRequest:
        # Если редактирование невозможно (например, это медиа-сообщение)
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass  # Если сообщение уже удалено

        sent_command_menu = await callback_query.message.answer(
            text=text_message,
            reply_markup=keyboard
        )
        await state.update_data(command_menu_id=sent_command_menu.message_id)
