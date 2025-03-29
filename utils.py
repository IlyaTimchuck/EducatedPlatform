from aiogram import Router
from bot_instance import bot


router = Router()


async def del_messages(user_id: int, lst_messages: list) -> None:
    for message_id in lst_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception as e:
            print(e)


