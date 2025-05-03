from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import app.bot.infrastructure.database as db


class CheckRegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # is_registered = db.users.user_is_unregistered()
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)
        if not is_registered:
            if isinstance(event, Message):
                await event.answer("❗ Чтобы пользоваться ботом, пожалуйста, сначала зарегистрируйтесь командой /start")
            elif isinstance(event, CallbackQuery):
                await event.answer("❗ Пожалуйста, зарегистрируйтесь командой /start", show_alert=True)
        return await handler(event, data)
