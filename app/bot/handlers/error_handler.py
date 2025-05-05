import logging
from app.bot.bot_instance import dp
from aiogram.types import ErrorEvent

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@dp.errors()
async def global_error_handler(event: ErrorEvent) -> bool:
    logger.exception(
        "Exception in handler: %s",
        event.exception,
        exc_info=event.exception
    )

    # Пример получения Update объекта (если нужно)
    update = event.update
    if update.message:
        user_id = update.message.from_user.id
        logger.error(f"Error in message from user {user_id}")

    return True  # Ошибка считается обработанной
