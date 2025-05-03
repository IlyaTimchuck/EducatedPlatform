import aiosqlite
from datetime import datetime



async def user_is_registered(user_id: int) -> bool:
    async with aiosqlite.connect('educated_platform.db') as con:
        result = await con.execute('''SELECT EXISTS 
        (SELECT 1 FROM users WHERE user_id = ?)''', (user_id,))
        row = await result.fetchone()
        return bool(row[0])


async def add_users(telegram_usernames: list, course_id: int) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        for username in telegram_usernames:
            await con.execute('INSERT INTO unregistered VALUES(?, ?)', (username, course_id))
        await con.commit()


async def registration_user(real_name: str, telegram_username: str, user_id: int, timezone: str, role: str) -> list:
    async with aiosqlite.connect('educated_platform.db') as con:
        tz_record = await (await con.execute(
            "SELECT timezone_id FROM timezones WHERE timezone = ?",
            (timezone,))).fetchone()

        if not tz_record:
            await con.execute(
                "INSERT INTO timezones (timezone) VALUES (?)",
                (timezone,)
            )
            tz_record = await (await con.execute("SELECT last_insert_rowid()")).fetchone()

        timezone_id = tz_record[0]
        date_of_joining = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lives = 3
        cursor = await con.execute('''SELECT c.course_id, c.course_title
                    FROM unregistered un
                    JOIN courses c ON c.course_id = un.course_id
                    WHERE un.telegram_username = ?''', (telegram_username,))
        course_data = (await cursor.fetchall())[0]
        if course_data:
            await con.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                              (real_name, telegram_username, user_id, course_data[0], timezone_id, date_of_joining,
                               lives, role))
            await con.execute('INSERT INTO history_of_lives VALUES(?, ?, ?, ?)', (user_id, None, None, '+3'))
            await con.execute('DELETE FROM unregistered WHERE telegram_username = ?', (telegram_username,))
            await con.commit()
        return course_data


async def delete_all_user_data(user_id: int) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        await con.execute("PRAGMA foreign_keys = ON;")
        await con.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        await con.commit()


async def get_users_by_course(course_id: int) -> list:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = '''SELECT u.*, c.course_title, t.timezone FROM users u 
                   JOIN courses c ON u.course_id = c.course_id
                   JOIN timezones t ON u.timezone_id = t.timezone_id
                   WHERE u.course_id=? AND u.role = ?'''
        async with con.execute(query, (course_id, 'student')) as cursor:
            users_data = await cursor.fetchall()
            return [dict(row) for row in users_data] if users_data else []


async def get_lives_user(user_id: int) -> int:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT lives FROM users WHERE user_id = ?', (user_id,))
        lives = await cursor.fetchone()
        return int(lives[0]) if lives else 0



async def get_data_user(user_id: int) -> dict:
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        async with con.cursor() as cursor:
            await cursor.execute('''SELECT * FROM users u 
                                    JOIN timezones t ON t.timezone_id = u.timezone_id
                                    WHERE u.user_id = ?''', (user_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            else:
                return {}
