import aiosqlite


async def get_metric_user(user_id: int) -> dict:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = """
               SELECT
                   COUNT(DISTINCT lp.exercise_id) AS right_answers,
                   COUNT(DISTINCT e.exercise_id) AS total_exercises
               FROM users u
               LEFT JOIN blocks b ON u.course_id = b.course_id
               LEFT JOIN tasks t ON t.block_id = b.block_id
               LEFT JOIN exercises e ON e.task_id = t.task_id
               LEFT JOIN learning_progress lp
                ON lp.user_id = u.user_id
                AND lp.exercise_id = e.exercise_id
                AND lp.right_answer = 1
               WHERE u.user_id = ?
               """

        async with con.execute(query, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return {'right_answers': 0, 'total_exercises': 0}
            return {'total_exercises': int(row['total_exercises']), 'right_answers': int(row['right_answers'])}


async def get_history_lives_user(user_id: int) -> list:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = '''SELECT h.lives_after_action, h.action, t.task_title
                   FROM history_of_lives h
                   LEFT JOIN tasks t ON t.task_id = h.task_id
                   WHERE h.user_id = ? OR h.user_id = ?'''
        async with con.execute(query, (user_id, 'all_users')) as cursor:
            result = await cursor.fetchall()
            return [dict(x) for x in result] if result else []
