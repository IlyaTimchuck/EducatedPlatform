from aiogram import Router
from bot_instance import bot

router = Router()


async def del_messages(user_id: int, lst_messages: list) -> None:
    for message_id in lst_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception as e:
            print(e)


async def send_notification_of_life_updates(updates: list, timezone_name: str) -> None:
    message_text = f'Была выполнена проверка дедлайнов для часового пояса {timezone_name}📅:\n'
    for update in updates:
        message_text += f"\n{update['real_name']}: {update['lives']}❤️ \u2192 {update['lives'] - 1}"
    await bot.send_message(chat_id=795508218, text=message_text)
