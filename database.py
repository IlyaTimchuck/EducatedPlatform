from datetime import datetime
import aiosqlite


def current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def create_db() -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute("DROP TABLE IF EXISTS unregistered")
        await con.execute("DROP TABLE IF EXISTS users")
        await con.execute("DROP TABLE IF EXISTS courses")
        await con.execute("DROP TABLE IF EXISTS blocks")
        await con.execute("DROP TABLE IF EXISTS tasks")
        await con.execute("DROP TABLE IF EXISTS exercises")
        await con.execute("DROP TABLE IF EXISTS learning_progress")
        await con.execute("DROP TABLE IF EXISTS sessions")
        await con.execute("DROP TABLE IF EXISTS changed_deadline")

        await con.execute('''CREATE TABLE IF NOT EXISTS unregistered (
            username TEXT,
            course_id INTEGER)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT,
            user_id INTEGER,
            course_id INTEGER,
            timezone STRING,
            date_of_joining TEXT,
            lives INTEGER,
            role TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS courses(
            course_tittle TEXT,
            course_id INTEGER PRIMARY KEY AUTOINCREMENT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS blocks (
            course_id INTEGER,
            block_number INTEGER, 
            block_id INTEGER PRIMARY KEY AUTOINCREMENT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS tasks (
            task_title TEXT,
            task_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            block_id INTEGER,
            verification TEXT,
            video_id TEXT,
            abstract_id TEXT,
            availability_files BOOL,
            deadline TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS exercises (
             task_id INTEGER,
             exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
             exercise_condition TEXT,
             exercise_answer TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS learning_progress (
             user_id INTEGER, 
             exercise_id INTEGER, 
             input_answer STRING, 
             right_answer BOOL, 
             session_id INTEGER)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_id INTEGER,
            is_completed BOOL,
            session_start TEXT,
            session_end TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS changed_deadlines (
            user_id INTEGER,
            task_id INTEGER,
            deadline STRING)''')

        await con.commit()


# Registration
async def create_course(course_tittle) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute('INSERT INTO courses (course_tittle) VALUES(?)', (course_tittle,))
        await con.commit()
        course_id = await get_course_id(course_tittle)
        await con.execute('INSERT INTO blocks (course_id, block_number) VALUES(?, ?)', (course_id, 1))
        await con.commit()


async def add_users(usernames: list, course_id: int) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        for user in usernames:
            await con.execute('INSERT INTO unregistered VALUES(?, ?)', (user, course_id))
        await con.commit()


async def user_is_unregistered(username: str) -> bool:
    async with aiosqlite.connect('educated_platform.db') as con:
        result = await con.execute('''SELECT EXISTS 
        (SELECT 1 FROM unregistered WHERE username = ?)''', (username,))
        row = await result.fetchone()
        return bool(row[0])


async def registration_user(username: str, user_id: int, timezone: str, role: str) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        date_of_joining = current_datetime()
        lives = 3
        cursor = await con.execute('SELECT course_id FROM unregistered WHERE username = ?', (username,))
        print(cursor)
        if cursor is not None:
            course_id = (await cursor.fetchone())[0]
            await con.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)',
                          (username, user_id, course_id, timezone, date_of_joining, lives, role))
            await con.execute('DELETE FROM unregistered WHERE username = ?', (username,))
            await con.commit()
        return cursor

# Other function
async def get_data_user(user_id: int) -> dict:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        async with con.cursor() as cursor:
            await cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            else:
                return {}


async def get_list_courses() -> list:
    """Возвращает список всех названий курсов из базы данных."""
    async with aiosqlite.connect('educated_platform.db') as con:
        async with con.execute('SELECT course_tittle FROM courses') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_blocks(course_id: int, current: bool = False) -> dict | int:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT block_number, block_id FROM blocks WHERE course_id = ?', (course_id,))
        rows = await cursor.fetchall()
        if current:
            if rows:
                return max(int(x[0]) for x in rows)
            else:
                return 0
        return {int(x[0]): int(x[1]) for x in rows}


async def get_course_id(course_tittle: str) -> int:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT course_id FROM courses WHERE course_tittle=?', (course_tittle,))
        course_id = await cursor.fetchone()
        return course_id[0]


# add_lesson
async def add_block(course_id: int, block_number: int) -> int:
    """Если блока не существует, то добавляет его. Всегда возвращает id блока"""
    async with aiosqlite.connect('educated_platform.db') as con:
        # Проверяем, существует ли блок
        if block_number not in await get_blocks(course_id):
            # Добавляем блок, если его нет
            await con.execute(
                'INSERT INTO blocks (course_id, block_number) VALUES (?, ?)',
                (course_id, block_number)
            )
            await con.commit()

        async with con.execute(
                'SELECT block_id FROM blocks WHERE course_id = ? AND block_number = ?',
                (course_id, block_number)) as cursor:
            row = await cursor.fetchone()
            return row[0]


async def add_task(task_title: str, block_id: int, verification: str, video_id: str, abstract_id: str,
                   availability_files: bool, deadline: str) -> int:
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute(
            'INSERT INTO tasks (task_title, block_id, verification, video_id, abstract_id, availability_files, deadline) VALUES(?, ?, ?, ?, ?, ?, ?)',
            (task_title, block_id, verification, video_id, abstract_id, availability_files, deadline))
        await con.commit()
        task_id = await con.execute('SELECT task_id FROM tasks WHERE task_title = ?', (task_title,))
        return (await task_id.fetchone())[0]


async def add_exercise(task_id: int, exercise_condition: str, exercise_answer=None) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        if exercise_answer is None:
            await con.execute(
                'INSERT INTO exercises (task_id, exercise_condition) VALUES(?, ?)',
                (task_id, exercise_condition))
        else:
            await con.execute(
                'INSERT INTO exercises (task_id, exercise_condition, exercise_answer) VALUES(?, ?, ?)',
                (task_id, exercise_condition, exercise_answer))
        await con.commit()


# mapping lesson
async def get_list_exercises(task_id: int) -> dict:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT verification FROM tasks WHERE task_id = ?', (task_id,))
        verification_row = await cursor.fetchone()
        verification = verification_row[0] if verification_row else None

        if verification == 'Автоматическая проверка':
            cursor = await con.execute(
                'SELECT exercise_condition, exercise_answer, exercise_id FROM exercises WHERE task_id = ?',
                (task_id,))
            result = await cursor.fetchall()
            return {num: (row[0], row[1], row[2]) for num, row in enumerate(result, 1)}
        else:
            cursor = await con.execute('SELECT exercise_condition, exercise_id FROM exercises WHERE task_id = ?',
                                       (task_id,))
            result = await cursor.fetchall()
            return {num: (row[0], row[1]) for num, row in enumerate(result, 1)}


async def get_list_tasks(block_id: int) -> dict:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        async with con.cursor() as cursor:
            cursor = await con.execute('SELECT task_title, task_id FROM tasks WHERE block_id=?',
                                       (block_id,))
            row = await cursor.fetchall()
            if row:
                return dict(row)
            else:
                return {}


async def mapping_task_status(user_id, task_id):
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = '''
            SELECT 
                COUNT(e.exercise_id) as total_exercises,
                SUM(lp.right_answer) as completed_exercises
            FROM exercises e
            LEFT JOIN learning_progress lp
                ON e.exercise_id = lp.exercise_id
                AND lp.user_id = ?
            WHERE e.task_id = ?
        '''
        async with con.execute(query, (user_id, task_id)) as cursor:
            result = await cursor.fetchone()

            if not result or result['total_exercises'] == 0:
                return '❌'

            return '✅' if result['completed_exercises'] == result['total_exercises'] else '⏳'


async def get_data_task(task_id: int):
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = '''SELECT * FROM tasks WHERE task_id = ?'''
        async with con.execute(query, (task_id,)) as cursor:
            task_data = await cursor.fetchone()
            return dict(task_data)


# Recording response(answer) user
async def get_progress_user(task_id: int, session_id: int = None) -> dict:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row

        query = """
        SELECT
            e.exercise_id,
            lp.input_answer,
            lp.right_answer
        FROM
            learning_progress AS lp
        JOIN
            exercises AS e ON lp.exercise_id = e.exercise_id
        WHERE
            e.task_id = ?
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


async def add_progress_user(user_id: int, task_id: int, homework: dict, results: dict, session_start: str,
                            session_end: str, is_completed: bool = False) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute(
            'INSERT INTO sessions (user_id, task_id, is_completed, session_start, session_end) VALUES (?, ?, ?, ?, ?)',
            (user_id, task_id, is_completed, session_start, session_end)
        )
        session_id = cursor.lastrowid

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
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = '''
            SELECT *
            FROM sessions
            WHERE user_id = ? AND task_id = ?
            ORDER BY session_id DESC
            LIMIT 1
        '''
        async with con.execute(query, (user_id, task_id)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}


async def get_all_users() -> list:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        async with con.execute('SELECT * FROM users') as cursor:
            result = await cursor.fetchall()
            return [dict(row) for row in result] if result else []


async def get_right_session(task_id: int) -> list:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        async with con.execute('SELECT * FROM sessions WHERE task_id = ? AND is_completed = 1', (task_id,)) as cursor:
            result = cursor.fetchall()
            return [dict(row) for row in result] if result else []


async def get_changed_deadline(task_id: int) -> list:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        async with con.execute('SELECT * FROM changed_deadline WHERE task_id = ?', (task_id,)) as cursor:
            result = cursor.fetchall()
            return [dict(row) for row in result] if result else []


async def get_next_deadline_info() -> dict | None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = """
            SELECT task_id, deadline
            FROM tasks
            WHERE deadline >= ?
            ORDER BY deadline ASC
            LIMIT 1
        """
        async with con.execute(query, (now,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
