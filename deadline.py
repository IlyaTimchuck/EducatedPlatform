import asyncio
from datetime import datetime

import pytz
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot_instance import bot, dp
from aiogram.fsm.storage.base import StorageKey
from google_table import google_client
import logging

import database as db
import keyboard as kb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def check_deadlines(timezone_id: int):
    timezone_name = (await db.get_timezones())[timezone_id]
    tz = pytz.timezone(timezone_name)
    now = datetime.now(tz).strftime("%Y-%m-%d")
    progress_users = await db.get_due_tasks_for_timezone(timezone_id, now)
    if progress_users:
        updates = await db.update_deadlines_and_lives_bulk(progress_users, timezone_id)
        await google_client.batch_set_lives_for_users(updates)
    logger.info('Проверка была выполнена, жизни в таблице обновлены')


async def send_deadline_reminder(timezone_id):
    deadline_today = await db.get_today_deadline_for_remind(timezone_id)
    if deadline_today:
        for deadline_data in deadline_today:
            text_message = f"Привет! Напоминаю, что сегодня в 0:00 дедлайн\nНазвание урока: {deadline_data['task_title']}"
            reminder_message = await bot.send_message(deadline_data['user_id'], text_message,
                                                      reply_markup=await kb.start_the_task_from_the_reminder(
                                                          deadline_data['course_id'],
                                                          deadline_data['task_id']))
            storage_key = StorageKey(bot_id=bot.id, chat_id=deadline_data['user_id'], user_id=deadline_data['user_id'])
            state = FSMContext(storage=dp.storage, key=storage_key)
            await state.update_data(reminder_message_id=reminder_message.message_id)
    logger.info('Напоминания разосланы')


async def update_jobs(scheduler):
    """Функция для обновления расписания задач для всех часовых поясов."""
    timezones = await db.get_timezones()

    logger.info(f"Updating timezone jobs for: {timezones}")
    for job in scheduler.get_jobs():
        if job.id.startswith("task_") or job.id.startswith("reminder_"):
            scheduler.remove_job(job.id)

    for timezone_id in timezones:
        tz_value = timezones[timezone_id]
        scheduler.add_job(
            check_deadlines,
            trigger=CronTrigger(hour=5, minute=36, timezone=tz_value),
            args=[timezone_id],
            id=f"task_{timezone_id}"
        )

        scheduler.add_job(
            send_deadline_reminder,
            trigger=CronTrigger(hour=5, minute=13, timezone=tz_value),
            args=[timezone_id],
            id=f"reminder_{timezone_id}"
        )

    logger.info("Timezone jobs updated.")


async def setup_monitoring():
    """Основная функция, которая инициализирует планировщик и устанавливает глобальное обновление"""
    scheduler = AsyncIOScheduler()
    scheduler.start()
    await update_jobs(scheduler)

    scheduler.add_job(
        update_jobs,
        trigger=CronTrigger(hour=5, minute=54, timezone="Europe/Moscow"),
        args=[scheduler],
        id="global_update"
    )

    await asyncio.Event().wait()
