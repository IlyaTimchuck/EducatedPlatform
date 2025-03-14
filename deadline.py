import asyncio
from datetime import datetime

from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram.types import Message
from aiogram import Bot

import state as st
import database as db
import keyboard as kb


async def check_deadlines(timezone_id: int):
    progress_users = await db.get_due_tasks_for_timezone(timezone_id, datetime.now().strftime("%Y-%m-%d"))
    if progress_users:
        await db.update_deadlines_and_lives_bulk(progress_users, timezone_id)
    print('Проверка была выполнена')


async def send_deadline_reminder(timezone_id, bot: Bot):
    deadline_today = await db.get_today_deadline(user_id=None, timezone_id=timezone_id)
    if deadline_today:
        for deadline_data in deadline_today:

            text_message = f"Привет! Напоминаю, что сегодня в 0:00 дедлайн\nНазвание урока: {deadline_data['task_title']}"
            await bot.send_message(deadline_data['user_id'], text_message,
                                   reply_markup=await kb.start_the_task_from_the_reminder(deadline_data['course_id'],
                                                                                          deadline_data['task_id']))
    print('Напоминания разосланы')

async def update_jobs(scheduler, bot: Bot):
    """Функция для обновления расписания задач для всех часовых поясов."""
    timezones = await db.get_timezones()
    courses = await db.get_list_courses()
    print("Updating timezone jobs for:", timezones)

    for job in scheduler.get_jobs():
        if job.id.startswith("task_") or job.id.startswith("reminder_"):
            scheduler.remove_job(job.id)

    for timezone_id in timezones:
        tz_value = timezones[timezone_id]
        scheduler.add_job(
            check_deadlines,
            trigger=CronTrigger(hour=11, minute=24, timezone=tz_value),
            args=[timezone_id],
            id=f"task_{timezone_id}"
        )

        scheduler.add_job(
            send_deadline_reminder,
            trigger=CronTrigger(hour=11, minute=23, timezone=tz_value),
            args=[timezone_id, bot],
            id=f"reminder_{timezone_id}"
        )


    print("Timezone jobs updated.")


async def setup_monitoring(bot: Bot):
    """Основная функция, которая инициализирует планировщик и устанавливает глобальное обновление"""
    scheduler = AsyncIOScheduler()
    scheduler.start()
    await update_jobs(scheduler, bot)

    scheduler.add_job(
        update_jobs,
        trigger=CronTrigger(hour=11, minute=22, timezone="Europe/Moscow"),
        args=[scheduler, bot],
        id="global_update"
    )

    await asyncio.Event().wait()

