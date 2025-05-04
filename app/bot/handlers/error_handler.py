import logging
from aiogram import types
from app.bot.bot_instance import dp

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@dp.errors()
async def global_error_handler(update: types.Update, exception: Exception) -> bool:
    logger.exception("Exception when handling update %s: %s", update, exception)
    return True