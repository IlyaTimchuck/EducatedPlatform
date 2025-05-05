from asyncio import run, create_task, CancelledError
from pathlib import Path
from app.bot.handlers import setup_handlers_router
from app.bot.bot_instance import bot, dp
from services.deadline import setup_monitoring
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
    # await db.courses.create_course('Тестовый')
    # course_id = await db.courses.get_course_id('Тестовый')
    # await db.users.add_users(['itimchuck'], None)
    # await db.users.add_users(['po1eena'], course_id)
    monitor_task = create_task(setup_monitoring())
    create_task(setup_google_polling_loop(google_client))
#     task_id = await db.tasks.add_task('Задание 16', course_id, True,
#                                 'BAACAgIAAxkBAAIFk2ecdMIb9MARHD1FCDBfDykIyVA8AAIQYAAChk_gSJ5yxpryw_xrNgQ',
#                                 'BQACAgIAAxkBAAID4GeW8STy6kbcasFhPk_ZNds1Q5u1AAKwdAACV7G4SHyUzFl8D_k0NgQ',
#                                 'https://drive.google.com/drive/u/0/folders/1lBvGtrV48Ad6kNhdpag2G9op6Nvy-Zin',
#                                 '2025-04-29')
#     await db.tasks.add_exercise(task_id,
#                           'Узлы с IP-адресами 157.220.185.237 и 157.220.184.230 принадлежат одной сети. Какое наименьшее количество IP-адресов, в двоичной записи которых ровно 15 единиц, может содержаться в этой сети?',
#                           '12')
#     await db.tasks.add_exercise(task_id,
#                           'Сеть, в которой содержится узел с IP-адресом 192.214.A.184, задана маской сети 255.255.255.224, где A - некоторое допустимое для записи IP-адреса число. Определите минимальное значение A, для которого для всех IP-адресов этой сети в двоичной записи IP-адреса суммарное количество единиц будет больше 15.',
#                           '43')
#     await db.tasks.add_exercise(task_id,
#                           '''В снежном королевстве существовала особая сеть, которая имела свой уникальный IP-адрес и маску.
# Однажды, Снежная Королева решила провести эксперимент, чтобы выяснить, сколько IP-адресов в её королевстве соответствуют определённому правилу. Она знала, что сеть ее королевства задается следующими данными:
# IP-адрес сети: 192.168.248.176
# Сетевая маска: 255.255.255.240
# Необходимо узнать, сколько в этой сети IP-адресов, для которых количество единиц и нулей в двоичной записи IP-адреса одинаково.''',
#                           '43')

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
