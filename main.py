from asyncio import run, create_task, CancelledError
from pathlib import Path
from app.bot.handlers import setup_handlers_router
from app.bot.bot_instance import bot, dp
from services.deadline_monitoring import setup_monitoring
from app.bot.infrastructure.api.google_table import setup_google_polling_loop, google_client
from app.bot.middlewares.lives_limiter import LifeCheckMiddleware
from app.bot.handlers.error_handler import global_error_handler
import app.bot.infrastructure.database as db


async def main() -> None:
    setup_handlers_router(dp)
    dp.message.middleware(LifeCheckMiddleware())
    dp.callback_query.middleware(LifeCheckMiddleware())
    BASE_DIR = Path(__file__).resolve().parent
    db_path = BASE_DIR / 'data' / 'educated_platform.db'
    await db.init_db.init_db(str(db_path))
    monitor_task = create_task(setup_monitoring())
    create_task(setup_google_polling_loop(google_client))

    try:
        await dp.start_polling(bot)
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except CancelledError:
            print("Monitoring task cancelled")
        await bot.session.close()


if __name__ == '__main__':
    run(main())
