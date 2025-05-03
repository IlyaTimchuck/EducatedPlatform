import aiosqlite


async def create_course(course_title) -> None:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('INSERT INTO courses (course_title) VALUES(?)', (course_title,))
        course_id = cursor.lastrowid
        await con.execute('INSERT INTO blocks (course_id, block_number) VALUES(?, ?)',
                          (course_id, 1))
        await con.commit()


async def get_list_courses() -> list:
    """Возвращает список всех названий курсов из базы данных."""
    async with aiosqlite.connect('educated_platform.db') as con:
        con.row_factory = aiosqlite.Row
        query = 'SELECT course_title, course_id FROM courses'
        async with con.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows] if rows else []


async def get_course_id(course_title: str) -> int:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT course_id FROM courses WHERE course_title=?', (course_title,))
        course_id = await cursor.fetchone()
        return course_id[0]


async def get_course_title(course_id: int) -> str:
    async with aiosqlite.connect('educated_platform.db') as con:
        cursor = await con.execute('SELECT course_title FROM courses WHERE course_id = ?', (course_id,))
        course_title = (await cursor.fetchone())[0]
        return course_title
