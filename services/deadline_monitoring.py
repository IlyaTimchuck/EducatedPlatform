from datetime import datetime, timedelta
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.bot.bot_instance import bot, dp
from aiogram.fsm.storage.base import StorageKey
from app.bot.infrastructure.api.google_table import google_client
from config import ADMIN_USER_ID
import logging
import pendulum
import asyncio
import pytz
import app.bot.infrastructure.database as db
import app.bot.keyboards as kb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def send_notification_of_life_updates(updates: list, timezone_name: str) -> None:
    message_text = f'Была выполнена проверка дедлайнов для часового пояса {timezone_name}📅:\n'
    for update in updates:
        message_text += f"\n{update['real_name']}: {update['lives']}❤️ \u2192 {update['lives'] - 1}❤️"
    await bot.send_message(chat_id=ADMIN_USER_ID, text=message_text)


async def check_deadlines(timezone_id: int):
    timezone_name = (await db.deadlines.get_timezones())[timezone_id]
    tz = pytz.timezone(timezone_name)
    now = datetime.now(tz).strftime("%Y-%m-%d")
    progress_users = await db.deadlines.get_due_tasks_for_timezone(timezone_id, now)
    if progress_users:
        updates = await db.deadlines.update_deadlines_and_lives_bulk(progress_users, timezone_id)
        await google_client.batch_set_lives_for_users(updates)
        await google_client.batch_set_deadlines_for_users(
            [(p['user_id'], p['task_id'],
              (datetime.strptime(p['deadline'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')) for p in
             progress_users])
        await send_notification_of_life_updates(progress_users, timezone_name)

    logger.info('Проверка была выполнена, жизни в таблице обновлены')


async def send_deadline_reminder(timezone_id):
    deadline_today = await db.deadlines.get_today_deadline_for_remind(timezone_id)
    if deadline_today:
        for deadline_data in deadline_today:
            text_message = f"Привет! Напоминаю, что сегодня в 0:00 дедлайн\nНазвание урока: {deadline_data['task_title']}"
            reminder_message = await bot.send_message(deadline_data['user_id'], text_message,
                                                      reply_markup=await kb.student_keyboards.start_the_task_from_the_reminder(
                                                          deadline_data['course_id'],
                                                          deadline_data['task_id']))
            storage_key = StorageKey(bot_id=bot.id, chat_id=deadline_data['user_id'], user_id=deadline_data['user_id'])
            state = FSMContext(storage=dp.storage, key=storage_key)
            await state.update_data(reminder_message_id=reminder_message.message_id)
    logger.info('Напоминания разосланы')


async def update_tz_jobs(scheduler: AsyncIOScheduler, timezone_id: str, tz_str: str):
    """
    Пересоздаёт задачи дедлайнов и напоминаний для одного часового пояса.
    """
    tz = pendulum.timezone(tz_str)
    for prefix in ("task_", "reminder_"):
        job_id = f"{prefix}{timezone_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass

    scheduler.add_job(
        check_deadlines,
        trigger=CronTrigger(hour=0, minute=0, timezone=tz),
        args=[timezone_id],
        id=f"task_{timezone_id}",
        replace_existing=True,
    )
    logger.info(f"Scheduled check_deadlines for {timezone_id} at 00:00 {tz_str}")
    scheduler.add_job(
        send_deadline_reminder,
        trigger=CronTrigger(hour=16, minute=30, timezone=tz),
        args=[timezone_id],
        id=f"reminder_{timezone_id}",
        replace_existing=True,
    )
    logger.info(f"Scheduled reminder for {timezone_id} at 16:30 {tz_str}")


async def update_all_timezones(scheduler: AsyncIOScheduler):
    """
    Обновляет задачи и ставит локальное обновление для каждой часовой зоны.
    """
    timezones = await db.deadlines.get_timezones()

    for timezone_id, tz_str in timezones.items():
        await update_tz_jobs(scheduler, timezone_id, tz_str)
        tz = pendulum.timezone(tz_str)
        scheduler.add_job(
            update_tz_jobs,
            trigger=CronTrigger(hour=23, minute=55, timezone=tz),
            args=[scheduler, timezone_id, tz_str],
            id=f"update_{timezone_id}",
            replace_existing=True,
        )
        logger.info(f"Scheduled update for {timezone_id} at 23:55 {tz_str}")


async def setup_monitoring():
    """
    Запускает планировщик и инициализирует локальные задачи.
    """
    scheduler = AsyncIOScheduler()
    scheduler.start()
    await update_all_timezones(scheduler)
    await asyncio.Event().wait()
