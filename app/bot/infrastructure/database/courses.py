from .init_db import get_db
import aiosqlite


async def create_course(course_title) -> None:
    con = get_db()
    cursor = await con.execute('INSERT INTO courses (course_title) VALUES(?)', (course_title,))
    course_id = cursor.lastrowid
    await con.execute('INSERT INTO blocks (course_id, block_number) VALUES(?, ?)',
                      (course_id, 1))
    await con.commit()
    return course_id


async def get_list_courses() -> list:
    """Возвращает список всех названий курсов из базы данных."""
    con = get_db()
    con.row_factory = aiosqlite.Row
    query = 'SELECT course_title, course_id FROM courses'
    async with con.execute(query) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows] if rows else []


async def get_course_id(course_title: str) -> int:
    con = get_db()
    cursor = await con.execute('SELECT course_id FROM courses WHERE course_title=?', (course_title,))
    course_id = await cursor.fetchone()
    return course_id[0]


async def get_course_title(course_id: int) -> str:
    con = get_db()
    cursor = await con.execute('SELECT course_title FROM courses WHERE course_id = ?', (course_id,))
    course_title = (await cursor.fetchone())[0]
    return course_title


async def change_course_name(new_course_name: str, course_id: int) -> None:
    con = get_db()
    await con.execute('UPDATE courses SET course_title = ? WHERE course_id = ?', (new_course_name, course_id))
    await con.commit()