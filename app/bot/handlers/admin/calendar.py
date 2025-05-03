from aiogram.types import CallbackQuery
from aiogram import Router, F

import app.bot.keyboards as kb

router = Router()


@router.callback_query(lambda c: c.data.startswith('prev_month') or c.data.startswith('next_month'))
async def month(callback_query: CallbackQuery):
    action, year, month = callback_query.data.split(":")
    year, month = int(year), int(month)
    if action == "prev_month":
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
    elif action == "next_month":
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    new_markup = await kb.admin_keyboards.create_task_keyboards.generate_calendar(year, month)
    await callback_query.message.edit_reply_markup(reply_markup=new_markup)

