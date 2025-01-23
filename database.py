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

        await con.execute('''CREATE TABLE IF NOT EXISTS unregistered (
            name TEXT,
            course_tittle TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT,
            user_id INTEGER,
            date_of_joining TEXT, 
            lives INTEGER,
            role TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS courses(
            course_tittle TEXT,
            course_id INTEGER PRIMARY KEY AUTOINCREMENT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS blocks (
            course_tittle TEXT,
            block_number INTEGER, 
            block_id INTEGER PRIMARY KEY AUTOINCREMENT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS tasks (
            task_tittle TEXT,
            task_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            block_id INTEGER,
            manual_verification BOOL,
            deadline TEXT)''')

        await con.execute('''CREATE TABLE IF NOT EXISTS exercises (
             task_id INTEGER,
             exercise_number INTEGER,
             exercise_condition TEXT,
             exercise_answer TEXT)''')

        await con.commit()


async def create_course(course_tittle):
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute('INSERT INTO courses (course_tittle) VALUES(?)', (course_tittle,))
        await con.execute('INSERT INTO blocks (course_tittle, block_number) VALUES(?, ?)', (course_tittle, 1))
        await con.commit()


async def add_users(usernames: list, course_tittle: str):
    async with aiosqlite.connect('educated_platform.db') as con:
        for user in usernames:
            await con.execute('INSERT INTO unregistered VALUES(?, ?)', (user, course_tittle))
        await con.commit()


async def user_in_unregistered(username: str):
    async with aiosqlite.connect('educated_platform.db') as con:
        result = await con.execute('''SELECT EXISTS 
        (SELECT 1 FROM unregistered WHERE name = ?)''', (username,))
        row = await result.fetchone()
        return bool(row[0])


async def registration_user(username: str, user_id: int, role: str):
    async with aiosqlite.connect('educated_platform.db') as con:
        date_of_joining = current_datetime()
        lives = 3
        await con.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?)',
                          (username, user_id, date_of_joining, lives, role))
        await con.commit()


async def get_data_user(user_id: int):
    async with aiosqlite.connect('educated_platform.db') as con:
        result = await con.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return await result.fetchall()


async def get_list_courses():
    async with aiosqlite.connect('educated_platform.db') as con:
        result = await con.execute('SELECT course_tittle FROM courses')
        return [x[0] for x in await result.fetchall()]


async def get_block(course_tittle: str, current: bool = False):
    async with aiosqlite.connect('educated_platform.db') as con:
        result = await con.execute('SELECT block_number FROM blocks WHERE course_tittle = ?', (course_tittle,))
        if current:
            return max(int(x[0]) for x in await result.fetchall())
        return [int(x[0]) for x in await result.fetchall()]


async def add_block(course_tittle: str, block_number: int):
    async with aiosqlite.connect('educated_platform.db') as con:
        if block_number not in await get_block(course_tittle):
            await con.execute('INSERT INTO blocks (course_tittle, block_number) VALUES(?, ?)',
                              (course_tittle, block_number))
            await con.commit()
            return con.execute('SELECT block_id FROM blocks WHERE course_tittle = ? AND block_number = ?',
                               (course_tittle, block_number))


async def add_task(task_tittle: str, block_id: int, manual_verification: bool, deadline: str):
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute(
            'INSERT INTO tasks (task_tittle, block_number, manual_verification, deadline) VALUES(?, ?, ?, ?)',
            (task_tittle, block_id, manual_verification, deadline))
        await con.commit()


async def add_exercise(task_id, exercise_number, exercise_condition, exercise_answer):
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute('INSERT INTO exercises VALUES(?, ?, ?, ?)',
                          (task_id, exercise_number, exercise_condition, exercise_answer))
        await con.commit()

