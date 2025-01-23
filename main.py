from asyncio import run
from aiogram import Bot, Dispatcher
from handlers.__init__ import setup_routers

import database as db

async def main() -> None:
    bot = Bot('7667517965:AAHlhkQRPurqi_0kZSiQ4e5H6eMKO5RbzP8')
    dp = Dispatcher()
    setup_routers(dp)
    await db.create_db()
    await db.create_course('Амиран')

    await db.add_users(['Тимчук Илья Артемович'], 'Амиран')
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    run(main())
