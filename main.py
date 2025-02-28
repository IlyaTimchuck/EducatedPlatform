from asyncio import run
from aiogram import Bot, Dispatcher
from handlers.__init__ import setup_routers
from callbacks.__init__ import setup_routers_callbacks
import database as db


async def main() -> None:
    bot = Bot('7667517965:AAGehj0I0nCwYFLBYTlpG2a4D5YQElh7qK0')
    dp = Dispatcher()
    setup_routers(dp)
    setup_routers_callbacks(dp)
    await db.create_db()
    await db.create_course('Тестовый')
    course_id = await db.get_course_id('Тестовый')
    await db.add_users(['f'], course_id)
    task_id = await db.add_task('Тестовый', course_id, 'Автоматическая проверка',
                                'BAACAgIAAxkBAAIFk2ecdMIb9MARHD1FCDBfDykIyVA8AAIQYAAChk_gSJ5yxpryw_xrNgQ',
                                'BQACAgIAAxkBAAID4GeW8STy6kbcasFhPk_ZNds1Q5u1AAKwdAACV7G4SHyUzFl8D_k0NgQ',
                                True, '31-01-2025')
    await db.add_exercise(task_id,
                          'Узлы с IP-адресами 157.220.185.237 и 157.220.184.230 принадлежат одной сети. Какое наименьшее количество IP-адресов, в двоичной записи которых ровно 15 единиц, может содержаться в этой сети?',
                          '12')
    await db.add_exercise(task_id,
                          'Сеть, в которой содержится узел с IP-адресом 192.214.A.184, задана маской сети 255.255.255.224, где A - некоторое допустимое для записи IP-адреса число. Определите минимальное значение A, для которого для всех IP-адресов этой сети в двоичной записи IP-адреса суммарное количество единиц будет больше 15.',
                          '43')
    await db.add_exercise(task_id,
                          '''В снежном королевстве существовала особая сеть, которая имела свой уникальный IP-адрес и маску.
Однажды, Снежная Королева решила провести эксперимент, чтобы выяснить, сколько IP-адресов в её королевстве соответствуют определённому правилу. Она знала, что сеть ее королевства задается следующими данными:
IP-адрес сети: 192.168.248.176
Сетевая маска: 255.255.255.240
Необходимо узнать, сколько в этой сети IP-адресов, для которых количество единиц и нулей в двоичной записи IP-адреса одинаково.''',
                          '43')


    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    run(main())
