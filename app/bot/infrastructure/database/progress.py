import aiosqlite
from .init_db import get_db
from datetime import datetime


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
    query = '''
        SELECT 
            COUNT(e.exercise_id) AS total_exercises,
            SUM(lp.right_answer) AS completed_exercises,
            COALESCE(cd.deadline, t.deadline) AS deadline
        FROM tasks t
        JOIN exercises e 
            ON t.task_id = e.task_id
        LEFT JOIN changed_deadlines cd 
            ON cd.task_id = t.task_id
           AND cd.user_id = ?
        LEFT JOIN learning_progress lp
            ON lp.exercise_id = e.exercise_id
           AND lp.user_id = ?
        WHERE t.task_id = ?
    '''
    async with con.execute(query, (user_id, user_id, task_id)) as cursor:
        row = await cursor.fetchone()
        if not row or row['total_exercises'] == 0:
            return '❌'
        total_exercises = row['total_exercises']
        completed_exercises = row['completed_exercises'] or 0
        deadline_str = row['deadline']
        deadline = None
        if deadline_str:
            try:
                if len(deadline_str) == 10:
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                else:
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                deadline = None
        if deadline and datetime.now() > deadline and completed_exercises < total_exercises:
            return '❌'
        if completed_exercises == total_exercises:
            return '✅'
        return '⏳'
