import aiosqlite
import pytz

from .init_db import get_db
from datetime import datetime, date


async def get_progress_user(task_id: int, session_id: int = None) -> dict:
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = """
    SELECT e.exercise_id, lp.input_answer, lp.right_answer
    FROM learning_progress AS lp
    JOIN exercises AS e ON lp.exercise_id = e.exercise_id
    WHERE e.task_id = ?
    """
    params = (task_id,)
    if session_id is not None:
        query += " AND lp.session_id = ?"
        params += (session_id,)
    async with con.execute(query, params) as cursor:
        result = await cursor.fetchall()
        if result:
            return {row['exercise_id']: {'input_answer': row['input_answer'],
                                         'status_input_answer': '✅' if row['right_answer'] else '❌'}
                    for row in result}
        else:
            return {}



async def mapping_task_status(user_id: int, task_id: int) -> str:
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = """
        SELECT
            COUNT(e.exercise_id)                 AS total_exercises,
            COALESCE(SUM(lp.right_answer), 0)    AS completed_exercises,
            COALESCE(cd.deadline, t.deadline)    AS raw_deadline,
            tz.timezone                          AS tz_name
        FROM tasks t
        LEFT JOIN exercises e
          ON e.task_id = t.task_id
        LEFT JOIN learning_progress lp
          ON lp.exercise_id = e.exercise_id
         AND lp.user_id = :user_id
        LEFT JOIN changed_deadlines cd
          ON cd.task_id = t.task_id
         AND cd.user_id = :user_id
        JOIN users u
          ON u.user_id = :user_id
        JOIN timezones tz
          ON tz.timezone_id = u.timezone_id
        WHERE t.task_id = :task_id
        GROUP BY t.task_id
    """
    params = {"user_id": user_id, "task_id": task_id}
    async with con.execute(query, params) as cur:
        row = await cur.fetchone()

    if not row:
        return "⏳"

    total = row["total_exercises"]
    done = row["completed_exercises"]

    if total == 0:
        return "⏳"
    if done >= total:
        return "✅"

    raw = (row["raw_deadline"] or "").strip()
    deadline_date = None

    if "." in raw:
        parts = raw.split(".")
        if len(parts) == 3:
            d, m, y = parts
            try:
                deadline_date = date(int(y), int(m), int(d))
            except ValueError:
                pass
    else:
        try:
            deadline_date = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            pass

    tz = pytz.timezone(row["tz_name"])
    today = datetime.now(tz).date()

    if deadline_date and today >= deadline_date:
        return "❌"
    return "⏳"