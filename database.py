from typing import Any, Coroutine
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import aiosqlite
from collections import defaultdict


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
        await con.execute("DROP TABLE IF EXISTS changed_deadlines")
        await con.execute("DROP TABLE IF EXISTS unique_timezones")
        await con.execute("DROP TABLE IF EXISTS history_of_lives")

        await con.execute('''CREATE TABLE IF NOT EXISTS unregistered (
            username TEXT,
            course_id INTEGER)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT,
            user_id INTEGER,
            course_id INTEGER,
            timezone_id TEXT,
            date_of_joining TEXT,
            lives INTEGER,
            role TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS courses(
            course_title TEXT,
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
             input_answer TEXT, 
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
                deadline TEXT,
                PRIMARY KEY (user_id, task_id))''')

        await con.execute('''CREATE TABLE IF NOT EXISTS unique_timezones (
            timezone TEXT,
            timezone_id INTEGER PRIMARY KEY AUTOINCREMENT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS history_of_lives (
            user_id INTEGER,
            task_id INTEGER,
            lives_after_action INTEGER,
            action TEXT)''')  # action: +1, +3, -1...

        await con.commit()


# Registration
async def create_course(course_title) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute('INSERT INTO courses (course_title) VALUES(?)', (course_title,))
        await con.commit()
        course_id = await get_course_id(course_title)
        await con.execute('INSERT INTO blocks (course_id, block_number) VALUES(?, ?)',
                          (course_id, 1))
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
        tz_record = await (await con.execute(
            "SELECT timezone_id FROM unique_timezones WHERE timezone = ?",
            (timezone,))).fetchone()

        if not tz_record:
            await con.execute(
                "INSERT INTO unique_timezones (timezone) VALUES (?)",
                (timezone,)
            )
            tz_record = await (await con.execute("SELECT last_insert_rowid()")).fetchone()

        timezone_id = tz_record[0]
        date_of_joining = current_datetime()
        lives = 3
        cursor = await con.execute('SELECT course_id FROM unregistered WHERE username = ?', (username,))
        course_id = await cursor.fetchone()
        if course_id:
            await con.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)',
                              (username, user_id, course_id[0], timezone_id, date_of_joining, lives, role))
            await con.execute('INSERT INTO history_of_lives VALUES(?, ?, ?, ?)', (user_id, None, None, '+3'))
            await con.execute('DELETE FROM unregistered WHERE username = ?', (username,))
            await con.commit()
        return course_id


# Other function
async def get_users_by_course(course_id: int) -> list:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT user_id FROM users WHERE course_id=? AND role = ?', (course_id, 'student'))
        result = await cursor.fetchall()
        return [x[0] for x in result] if result else []


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
        con.row_factory = aiosqlite.Row
        query = 'SELECT course_title, course_id FROM courses'
        async with con.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows] if rows else []


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


async def get_course_id(course_title: str) -> int:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT course_id FROM courses WHERE course_title=?', (course_title,))
        course_id = await cursor.fetchone()
        return course_id[0]


async def check_block_exists(course_id: int, block_number: int) -> int:
    async with aiosqlite.connect('educated_platform.db') as con:
        async with con.execute(
                '''SELECT b.block_id
                    FROM blocks b
                    WHERE b.course_id = ? AND b.block_number = ?
                ''',
                (course_id, block_number)
        ) as cursor:
            result = await cursor.fetchall()
            return int(result[0][0]) if result else None


async def create_block(course_id: int, block_number: int) -> int:
    """Создает новый блок и возвращает его ID"""
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute(
            'INSERT INTO blocks (course_id, block_number) VALUES (?, ?)',
            (course_id, block_number)
        )
        await con.commit()
        return cursor.lastrowid


async def add_task(task_title: str, block_id: int, verification: str, video_id: str, abstract_id: str,
                   availability_files: bool, deadline: str) -> int:
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute(
            'INSERT INTO tasks (task_title, block_id, verification, video_id, abstract_id, availability_files, deadline) VALUES(?, ?, ?, ?, ?, ?, ?)',
            (task_title, block_id, verification, video_id, abstract_id, availability_files, deadline))
        await con.commit()
        task_id = await con.execute('SELECT task_id FROM tasks WHERE video_id = ?', (video_id,))
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


from datetime import datetime


async def mapping_task_status(user_id: int, task_id: int) -> str:
    async with aiosqlite.connect('educated_platform.db') as con:
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

            # Парсим дедлайн с учетом того, что он может содержать только дату
            deadline = None
            if deadline_str:
                try:
                    # Если строка содержит только дату (YYYY-MM-DD)
                    if len(deadline_str) == 10:
                        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                    else:
                        deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Если формат не соответствует ни одному из ожидаемых вариантов,
                    # можно залогировать ошибку или задать deadline = None
                    deadline = None

            # Если дедлайн задан и прошёл, и не все упражнения выполнены до дедлайна – возвращаем ❌
            if deadline and datetime.now() > deadline and completed_exercises < total_exercises:
                return '❌'

            # Если все упражнения выполнены – возвращаем ✅
            if completed_exercises == total_exercises:
                return '✅'

            # Иначе возвращаем статус "в процессе" – ⏳
            return '⏳'


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


async def get_timezones() -> dict:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = 'SELECT * FROM unique_timezones'
        async with await con.execute(query) as cursor:
            rows = await cursor.fetchall()
            return {row["timezone_id"]: row["timezone"] for row in rows} if rows else {}


async def get_due_tasks_for_timezone(timezone_id: int, current_date: str) -> list:
    """
    Возвращает список строк, где каждая строка содержит:
      - user_id: идентификатор пользователя
      - task_id: идентификатор задания
      - actual_deadline: дедлайн, учитывающий changed_deadlines
      - is_completed: статус завершения сессии (может быть None, если сессии нет)
    Для заданий, дедлайн которых равен current_date,
    и пользователей с заданным timezone_id.
    Возвращает только тех пользователей, у которых нет сессий с is_completed = 1.
    """
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = """SELECT
                u.user_id,
                t.task_id,
                u.lives
            FROM tasks t
            JOIN blocks b ON b.block_id = t.block_id
            JOIN users u ON u.course_id = b.course_id
            LEFT JOIN changed_deadlines cd ON cd.task_id = t.task_id AND cd.user_id = u.user_id
            LEFT JOIN sessions s ON s.task_id = t.task_id AND s.user_id = u.user_id
            WHERE u.timezone_id = ?
              AND COALESCE(cd.deadline, t.deadline) = ?
            GROUP BY u.user_id, t.task_id
            HAVING MAX(s.is_completed) IS NULL OR MAX(s.is_completed) = 0
                    """

        async with con.execute(query, (timezone_id, current_date)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows] if rows else []


async def update_deadlines_and_lives_bulk(updates: list, timezone_id: int) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        # Получаем значение timezone из unique_timezones
        async with con.execute("SELECT timezone FROM unique_timezones WHERE timezone_id = ?", (timezone_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                raise ValueError(f"Timezone with id {timezone_id} not found")
            tz_value = str(row[0])

        # Вычисляем новый дедлайн как завтрашнюю дату с учетом timezone
        new_deadline = (datetime.now(tz=ZoneInfo(tz_value)) + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        await con.execute("BEGIN TRANSACTION")
        try:
            # Группируем уникальные пары (user_id, task_id)
            unique_pairs = {(u["user_id"], u["task_id"]) for u in updates}

            # Обновляем дедлайны в changed_deadlines с использованием UPSERT
            await con.executemany(
                """INSERT INTO changed_deadlines (user_id, task_id, deadline)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id, task_id) 
                   DO UPDATE SET deadline = excluded.deadline""",
                [(user_id, task_id, new_deadline) for user_id, task_id in unique_pairs]
            )

            # Считаем количество списаний для каждого пользователя
            user_counts = defaultdict(int)
            for u in updates:
                user_counts[u["user_id"]] += 1

            # Обновляем жизни для каждого пользователя
            await con.executemany(
                """UPDATE users 
                   SET lives = MAX(lives - ?, 0)
                   WHERE user_id = ?""",
                [(count, user_id) for user_id, count in user_counts.items()]
            )

            # Готовим записи для истории списаний.
            # Предполагаем, что в updates для каждого пользователя поле "lives" содержит текущее значение до списания.
            history_records = []
            for u in updates:
                # Если один пользователь появляется несколько раз, мы будем добавлять несколько записей.
                new_lives = u["lives"] - user_counts[u["user_id"]]
                history_records.append((u["user_id"], u["task_id"], new_lives, '-1'))

            # Выполняем пакетную вставку в history_of_lives
            await con.executemany(
                "INSERT INTO history_of_lives VALUES (?, ?, ?, ?)",
                history_records
            )

            await con.commit()

        except Exception as e:
            await con.rollback()
            raise e


async def get_today_deadline(user_id: int | None = None, timezone_id: int | None = None) -> None | list:
    async with aiosqlite.connect('educated_platform.db') as con:
        if user_id:
            current_deadline = datetime.now().strftime("%Y-%m-%d")
            query = '''SELECT t.task_title, u.lives
                           FROM tasks t 
                           JOIN blocks b ON b.block_id = t.block_id
                           JOIN users u ON b.course_id = u.course_id
                           WHERE u.user_id = ? AND t.deadline = ? 
                           '''
            con.row_factory = aiosqlite.Row
            async with con.execute(query, (user_id, current_deadline)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows] if rows else []
        elif timezone_id:
            query = '''SELECT u.user_id, u.course_id, t.task_id, t.task_title, b.block_id
                       FROM tasks t
                       JOIN blocks b ON b.block_id = t.block_id
                       JOIN users u ON u.course_id = b.block_id
                       WHERE u.timezone_id = ?'''
            con.row_factory = aiosqlite.Row
            async with con.execute(query, (timezone_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows] if rows else []


async def get_today_new_block() -> list:
    current_date = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT course_id FROM blocks WHERE block_start=?', current_date)
        rows = await cursor.fetchall()
        return [row[0] for row in rows] if rows else []


async def update_lives(course_id):
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute('UPDATE users SET lives = ? WHERE course_id = ? AND lives != ?', (3, course_id, 0))
        await con.execute('''
                   DELETE FROM history_of_lives
                   WHERE user_id IN (
                       SELECT user_id FROM users WHERE course_id = ?
                   )''', (course_id,))
        await con.execute('INSERT INTO history_of_lives VALUES(?, ?, ?, ?)', ('all_users', None, 3, '+3'))
        await con.commit()


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
