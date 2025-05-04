from typing import Union
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from app.bot.bot_instance import bot
import app.bot.states.state as st
import app.bot.keyboards as kb

router = Router()


@router.message(Command(commands=['start']))
async def start(message: types.Message, state: FSMContext):
    message_user = message.message_id
    sent_message = await message.answer(
        f'Привет! Чтобы зарегистрироваться на курс мне необходимо знать твое имя и фамилию. Отправь мне их сообщением')
    await state.set_state(st.Registration.get_name_user)
    await state.update_data(reg_msg_for_deletion=[sent_message.message_id, message_user])


@router.message(Command(commands=['command_menu']))
@router.callback_query(F.data == "attempt_to_log_in")
async def command_menu(update: Union[Message, CallbackQuery], state: FSMContext):
    state_data = await state.get_data()
    user_id = update.from_user.id
    if isinstance(update, CallbackQuery):
        block_messages_user = state_data['block_messages_user']
        for block_message_user in block_messages_user:
            await bot.delete_message(chat_id=user_id, message_id=block_message_user)
        await bot.delete_message(chat_id=user_id, message_id=state_data['block_message_id'])
        state_data.pop('block_message_id')
        await update.answer('Блокировка была снята!',
                            show_alert=True)
    message_menu_id = state_data.get('command_menu_id')
    message_abstract_id = state_data.get('message_abstract_id')
    session_start = state_data.get('session_start')
    session_end = state_data.get('session_end')
    reminder_message_id = state_data.get('reminder_message_id')
    notification_about_new_task_message_id = state_data.get('notification_about_new_task_message_id')
    messages_getting_file_work = state_data.get('messages_getting_file_work')
    file_work_message_id = state_data.get('message_file_work_id')
    if message_menu_id:
        await bot.delete_message(chat_id=user_id, message_id=message_menu_id)
    if message_abstract_id:
        await bot.delete_message(chat_id=user_id, message_id=message_abstract_id)
    if reminder_message_id:
        await bot.delete_message(chat_id=user_id, message_id=reminder_message_id)
    if notification_about_new_task_message_id:
        await bot.delete_message(chat_id=user_id, message_id=notification_about_new_task_message_id)
    if messages_getting_file_work:
        for message_id in messages_getting_file_work:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
    if file_work_message_id:
        await bot.delete_message(chat_id=user_id, message_id=file_work_message_id)
    elif session_start and not session_end:
        await bot.delete_message(chat_id=user_id, message_id=state_data['homework_message_id'])

    text_message, keyboard = await kb.main_menu.send_command_menu(user_id)
    new_command_menu_id = await bot.send_message(text=text_message, chat_id=user_id, reply_markup=keyboard)
    await state.clear()
    await state.set_state(st.MappingExercise.mapping_command_menu)
    await state.update_data(command_menu_id=new_command_menu_id.message_id)


@router.callback_query(lambda call: call.data in ['back_student', 'back_admin'])
async def process_back_button(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    text_message, keyboard = await kb.main_menu.send_command_menu(callback_query.from_user.id)
    state_data = await state.get_data()
    abstract = state_data.get('message_abstract_id')
    file_work_message_id = state_data.get('message_file_work_id')
    if abstract:
        await callback_query.message.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=abstract)
        state_data.pop('message_abstract_id')
    if file_work_message_id:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=file_work_message_id)
        state_data.pop('message_file_work_id')
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
            pass

        sent_command_menu = await callback_query.message.answer(
            text=text_message,
            reply_markup=keyboard
        )
        await state.update_data(command_menu_id=sent_command_menu.message_id)
