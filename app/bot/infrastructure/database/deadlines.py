from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import aiosqlite
from collections import defaultdict
from .init_db import get_db
import pytz


async def get_timezones() -> dict:
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = 'SELECT * FROM timezones'
    async with await con.execute(query) as cursor:
        rows = await cursor.fetchall()
        return {row["timezone_id"]: row["timezone"] for row in rows} if rows else {}


async def change_deadline(user_id: int, task_id: int, new_date: str) -> None:
    con = get_db()
    await con.execute('INSERT INTO changed_deadlines VALUES(?, ?, ?)', (user_id, task_id, new_date))
    await con.commit()


async def get_due_tasks_for_timezone(timezone_id: int, current_date: str) -> list:
    """
    Возвращает список словарей, где каждый словарь содержит:
      - user_id: идентификатор пользователя
      - real_name: фамилия и имя пользователя
      - task_id: идентификатор задания
      - actual_deadline: дедлайн, учитывающий changed_deadlines
      - is_completed: статус завершения сессии (может быть None, если сессии нет)
    Для заданий, дедлайн которых равен current_date,
    и пользователей с заданным timezone_id.
    Возвращает только тех пользователей, у которых нет сессий с is_completed = 1.
    """
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = """SELECT
            u.user_id,
            u.real_name,
            t.task_id,
            t.task_title,
            u.lives
        FROM tasks t
        JOIN blocks b ON b.block_id = t.block_id
        JOIN users u ON u.course_id = b.course_id
        LEFT JOIN changed_deadlines cd ON cd.task_id = t.task_id AND cd.user_id = u.user_id
        LEFT JOIN sessions s ON s.task_id = t.task_id AND s.user_id = u.user_id
        WHERE u.timezone_id = ?
          AND u.role = 'student'
          AND COALESCE(cd.deadline, t.deadline) = ?
        GROUP BY u.user_id, t.task_id
        HAVING MAX(s.is_completed) IS NULL OR MAX(s.is_completed) = 0
                """
    async with con.execute(query, (timezone_id, current_date)) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows] if rows else []


async def update_deadlines_and_lives_bulk(updates: list, timezone_id: int) -> list:
    con = get_db()
    async with con.execute("SELECT timezone FROM timezones WHERE timezone_id = ?", (timezone_id,)) as cur:
        row = await cur.fetchone()
        if not row:
            raise ValueError(f"Timezone with id {timezone_id} not found")
        tz_value = str(row[0])
    new_deadline = (datetime.now(tz=ZoneInfo(tz_value)) + timedelta(days=1)).strftime("%Y-%m-%d")
    await con.execute("BEGIN TRANSACTION")
    try:
        unique_pairs = {(u["user_id"], u["task_id"]) for u in updates}
        await con.executemany(
            """INSERT INTO changed_deadlines (user_id, task_id, deadline)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, task_id) 
               DO UPDATE SET deadline = excluded.deadline""",
            [(user_id, task_id, new_deadline) for user_id, task_id in unique_pairs]
        )
        user_counts = defaultdict(int)
        for u in updates:
            user_counts[u["user_id"]] += 1
        await con.executemany(
            """UPDATE users 
               SET lives = MAX(lives - ?, 0)
               WHERE user_id = ?""",
            [(count, user_id) for user_id, count in user_counts.items()]
        )
        history_records = []
        for u in updates:
            new_lives = u["lives"] - user_counts[u["user_id"]]
            history_records.append((u["user_id"], u["task_id"], new_lives, '-1'))
        await con.executemany(
            "INSERT INTO history_of_lives VALUES (?, ?, ?, ?)",
            history_records
        )
        await con.commit()
        return [(record[0], record[2]) for record in history_records]
    except Exception as e:
        await con.rollback()
        raise e


async def get_today_deadline_for_remind(timezone_id: int) -> list:
    con = get_db()
    timezone_name = (await get_timezones())[timezone_id]
    tz = pytz.timezone(timezone_name)
    now = datetime.now(tz)
    current_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    query = '''SELECT u.user_id, u.course_id, t.task_id, t.task_title, b.block_id
                FROM tasks t
                JOIN blocks b ON t.block_id = b.block_id
                JOIN users u ON b.course_id = u.course_id
                WHERE u.timezone_id = ? AND t.deadline = ?'''
    con.row_factory = aiosqlite.Row
    async with con.execute(query, (timezone_id, current_date)) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows] if rows else []


async def get_today_deadline_for_keyboard(user_id: int):
    con = get_db()
    con.row_factory = aiosqlite.Row
    async with con.execute(
            """
            SELECT t.timezone
              FROM timezones t
              JOIN users u ON t.timezone_id = u.timezone_id
             WHERE u.user_id = ?
            """,
            (user_id,)
    ) as cur_tz:
        tz_row = await cur_tz.fetchone()
    if not tz_row:
        return []
    tz = pytz.timezone(tz_row['timezone'])
    now = datetime.now(tz)
    tomorrow_str = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    query = """
        SELECT
            u.user_id,
            u.course_id,
            t.task_id,
            t.task_title,
            b.block_id
        FROM tasks t
        JOIN blocks b
          ON t.block_id = b.block_id
        JOIN users u
          ON b.course_id = u.course_id
        LEFT JOIN changed_deadlines cd
          ON cd.task_id = t.task_id
         AND cd.user_id = u.user_id
        WHERE u.user_id = ?
          AND COALESCE(cd.deadline, t.deadline) = ?
    """
    async with con.execute(query, (user_id, tomorrow_str)) as cur_tasks:
        rows = await cur_tasks.fetchall()
    return [dict(r) for r in rows] if rows else []


async def update_lives_for_user(user_id: int, new_count_lives: int) -> None:
    con = get_db()
    cursor = await con.execute('SELECT lives FROM users WHERE user_id = ?', (user_id,))
    old_count_lives = (await cursor.fetchone())[0]
    await con.execute('UPDATE users SET lives = ? WHERE user_id = ?', (new_count_lives, user_id))
    if old_count_lives > new_count_lives:
        change_operation = '-'
        difference_lives = old_count_lives - new_count_lives
    else:
        change_operation = '+'
        difference_lives = new_count_lives - old_count_lives
    action = change_operation + str(difference_lives)
    await con.execute('INSERT INTO history_of_lives VALUES(?, ?, ?, ?)', (user_id, None, new_count_lives, action))
    await con.commit()
