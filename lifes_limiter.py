from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Callable, Awaitable, Dict, Any
import database as db
import keyboard as kb


class LifeCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        lives = await db.get_lifes_user(user.id)
        if lives <= 0:

            if not (await db.get_data_user(user.id)):
                return await handler(event, data)

            if isinstance(event, CallbackQuery):
                await event.answer(
                    "❌ У вас закончились жизни. Доступ к курсу заблокирован. Обратитесь к администратору.",
                    show_alert=True
                )
            else:
                state: FSMContext = data.get("state")
                state_data = await state.get_data() if state else {}
                # Message
                if not state_data.get("blocked_shown"):
                    block_message_user = state_data.get('block_messages_user', [])
                    block_message_user.append(event.message_id)
                    block_message = await event.answer(
                        "❌ У вас закончились жизни. Доступ к курсу заблокирован. Обратитесь к администратору.",
                        reply_markup=kb.block_button)
                    await state.update_data(blocked_shown=True, block_message_id=block_message.message_id, block_messages_user=block_message_user)
            return

        return await handler(event, data)
