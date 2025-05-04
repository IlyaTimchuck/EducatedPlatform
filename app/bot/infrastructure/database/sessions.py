import aiosqlite
from .init_db import get_db

async def add_progress_user(user_id: int, task_id: int, homework: dict, results: dict, session_start: str,
                            session_end: str, file_work_id: str, is_completed: bool) -> None:
    con = get_db()
    cursor = await con.execute(
        'INSERT INTO sessions (user_id, task_id, is_completed, session_start, session_end) VALUES (?, ?, ?, ?, ?)',
        (user_id, task_id, is_completed, session_start, session_end)
    )
    session_id = cursor.lastrowid
    if file_work_id:
        await con.execute('INSERT INTO session_files VALUES(?, ?)', (session_id, file_work_id))
    for exercise_num in homework:
        _, right_answer, exercise_id = homework[exercise_num]
        input_answer = results.get(exercise_num, {}).get('input_answer', None)
        if input_answer is not None:
            is_correct = (str(input_answer).strip() == str(right_answer).strip())
            await con.execute(
                'INSERT INTO learning_progress VALUES(?, ?, ?, ?, ?)',
                (user_id, exercise_id, input_answer, is_correct, session_id)
            )
    await con.commit()

async def get_last_session(user_id: int, task_id: int) -> dict:
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = '''
        SELECT * FROM sessions s
        LEFT JOIN session_files sf ON sf.session_id = s.session_id
        WHERE s.user_id = ? AND s.task_id = ?
        ORDER BY session_id DESC LIMIT 1'''
    async with con.execute(query, (user_id, task_id)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else {}