from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram import Router, F

import state as st
import database as db
import keyboard as kb

router = Router()


@router.callback_query(F.data == 'list_lives')
async def opening_list_lives(callback_query: CallbackQuery):
    await callback_query.answer()
    history_lives_user = await db.get_history_lives_user(callback_query.from_user.id)
    text_message = "📝 История изменений жизней:\n\n"
    for change in history_lives_user:
        action = change['action']
        if action == '-1':
            if change['task_title']:
                text_message += f'{action}❤️ Просрочен дедлайн к уроку {change['task_title']}\n'
            else:
                text_message += f'{action}❤️ Индивидуальное обновление жизней\n'
        elif action == '+3':
            text_message += f'{action}❤️ Новый блок!\n'
        else:
            text_message += f'{action}❤️ Индивидуальное обновление жизней\n'
    await callback_query.message.edit_text(text=text_message, reply_markup=kb.back_button_admin)
