import aiosqlite
from .init_db import get_db


async def add_task(task_title: str, block_id: int, file_work: bool, video_id: str, abstract_id: str,
                   link_files: str | None, deadline: str) -> int:
    con = get_db()
    await con.execute(
        '''INSERT INTO tasks (task_title, block_id, file_work, video_id, abstract_id, link_files, deadline)
                                                                    VALUES(?, ?, ?, ?, ?, ?, ?)''',
        (task_title, block_id, file_work, video_id, abstract_id, link_files, deadline))
    await con.commit()
    task_id = await con.execute('SELECT task_id FROM tasks WHERE video_id = ?', (video_id,))
    return (await task_id.fetchone())[0]


async def get_data_task(user_id: int, task_id: int):
    con = get_db()
    con.row_factory = aiosqlite.Row
    query1 = 'SELECT * FROM tasks WHERE task_id = ?'
    async with con.execute(query1, (task_id,)) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        task_data = dict(row)
    query2 = 'SELECT deadline FROM changed_deadlines WHERE user_id = ? AND task_id = ?'
    async with con.execute(query2, (user_id, task_id)) as cursor:
        row = await cursor.fetchone()
        changed_deadline = row['deadline'] if row else None
    if changed_deadline:
        task_data['deadline'] = changed_deadline
    return task_data


async def add_exercise(task_id: int, exercise_condition: str, exercise_answer=None) -> None:
    con = get_db()
    if exercise_answer is None:
        await con.execute(
            'INSERT INTO exercises (task_id, exercise_condition) VALUES(?, ?)',
            (task_id, exercise_condition))
    else:
        await con.execute(
            'INSERT INTO exercises (task_id, exercise_condition, exercise_answer) VALUES(?, ?, ?)',
            (task_id, exercise_condition, exercise_answer))
    await con.commit()


async def get_list_exercises(task_id: int) -> dict:
    con = get_db()
    cursor = await con.execute(
        'SELECT exercise_condition, exercise_answer, exercise_id FROM exercises WHERE task_id = ?',
        (task_id,))
    result = await cursor.fetchall()
    return {num: (row[0], row[1], row[2]) for num, row in enumerate(result, 1)}


async def get_list_tasks(block_id: int) -> dict:
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = 'SELECT task_title, task_id FROM tasks WHERE block_id=?'
    async with con.execute(query, (block_id,)) as cursor:
        row = await cursor.fetchall()
        if row:
            return dict(row)
        else:
            return {}


async def get_last_task(user_id):
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = '''SELECT u.course_id, t.block_id, t.task_id
                   FROM users u
                   JOIN blocks b ON u.course_id = b.course_id
                   JOIN tasks t ON b.block_id = t.block_id
                   WHERE u.user_id = ?
                   ORDER BY t.deadline DESC 
                   LIMIT 1;'''
    async with con.execute(query, (user_id,)) as cursor:
        last_task = await cursor.fetchone()
        return dict(last_task) if last_task else {}
