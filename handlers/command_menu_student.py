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
