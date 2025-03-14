from aiogram.filters import Command
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
import state as st
import database as db
import keyboard as kb

router = Router()

@router.message(Command(commands=['start']))
async def start(message: types.Message, state: FSMContext):
    await message.answer('Привет! Чтобы начать обучение отправь мне свои ФИО')
    await state.set_state(st.Registration.get_name_user)

@router.message(Command(commands=['command_menu']))
async def command_menu(message: types.Message, state: FSMContext):
    message_menu_id = (await state.get_data()).get('message_menu_id', None)
    # if message_menu_id:
        # await bot.delete_message()
    text_message, keyboard = await kb.send_command_menu(message.from_user.id)
    await message.answer(text_message, reply_markup=keyboard)


@router.callback_query(lambda call: call.data in ['back_student', 'back_admin'])
async def process_back_button(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    text_message, keyboard = await kb.send_command_menu(callback_query.from_user.id)
    state_data = await state.get_data()
    abstract = state_data.get('message_abstract_id', False)
    if abstract:
        await callback_query.message.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=abstract)
    await state.clear()
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

        await callback_query.message.answer(
            text=text_message,
            reply_markup=keyboard
        )