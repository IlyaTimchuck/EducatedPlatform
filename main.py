from asyncio import run, create_task, CancelledError
from aiogram import Bot, Dispatcher
from handlers.__init__ import setup_routers
from callbacks.__init__ import setup_routers_callbacks
from deadline import setup_monitoring
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
    await db.add_users(['try_user'], course_id)
    await db.create_block(course_id, 2)
    monitor_task = create_task(setup_monitoring(bot))
    task_id = await db.add_task('Задание 16', course_id, 'Автоматическая проверка',
                                'BAACAgIAAxkBAAIFk2ecdMIb9MARHD1FCDBfDykIyVA8AAIQYAAChk_gSJ5yxpryw_xrNgQ',
                                'BQACAgIAAxkBAAID4GeW8STy6kbcasFhPk_ZNds1Q5u1AAKwdAACV7G4SHyUzFl8D_k0NgQ',
                                True, '2025-03-14')
    await db.add_exercise(task_id,
                          'Узлы с IP-адресами 157.220.185.237 и 157.220.184.230 принадлежат одной сети. Какое наименьшее количество IP-адресов, в двоичной записи которых ровно 15 единиц, может содержаться в этой сети?',
                          '12')
    await db.add_exercise(task_id,
                          'Сеть, в которой содержится узел с IP-адресом 192.214.A.184, задана маской сети 255.255.255.224, где A - некоторое допустимое для записи IP-адреса число. Определите минимальное значение A, для которого для всех IP-адресов этой сети в двоичной записи IP-адреса суммарное количество единиц будет больше 15.',
                          '43')
    await db.add_exercise(task_id ,
                          '''В снежном королевстве существовала особая сеть, которая имела свой уникальный IP-адрес и маску.
Однажды, Снежная Королева решила провести эксперимент, чтобы выяснить, сколько IP-адресов в её королевстве соответствуют определённому правилу. Она знала, что сеть ее королевства задается следующими данными:
IP-адрес сети: 192.168.248.176
Сетевая маска: 255.255.255.240
Необходимо узнать, сколько в этой сети IP-адресов, для которых количество единиц и нулей в двоичной записи IP-адреса одинаково.''',
                          '43')

    # task_id1 = await db.add_task('Тестовый 2', course_id, 'Автоматическая проверка',
    #                             'BAACAgIAAxkBAAIFk2ecdMIb9MARHD1FCDBfDykIyVA8AAIQYAAChk_gSJ5yxpryw_xrNgQ',
    #                             'BQACAgIAAxkBAAID4GeW8STy6kbcasFhPk_ZNds1Q5u1AAKwdAACV7G4SHyUzFl8D_k0NgQ',
    #                             True, '2025-03-10')
    # await db.add_exercise(task_id1,
    #                       '''Хуй попа жопа''',
    #                       'сиси')
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
