from .init_db import get_db
from datetime import datetime


async def get_blocks(course_id: int, current: bool = False) -> dict | int:
    con = get_db()
    cursor = await con.execute('SELECT block_number, block_id FROM blocks WHERE course_id = ?', (course_id,))
    rows = await cursor.fetchall()
    if current:
        if rows:
            return max(int(x[0]) for x in rows)
        else:
            return 0
    return {int(x[0]): int(x[1]) for x in rows}


async def check_block_exists(course_id: int, block_number: int) -> int:
    con = get_db()
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
    con = get_db()
    cursor = await con.execute(
        'INSERT INTO blocks (course_id, block_number) VALUES (?, ?)',
        (course_id, block_number)
    )
    await con.commit()
    return cursor.lastrowid


async def get_today_new_block() -> list:
    current_date = datetime.now().strftime("%Y-%m-%d")
    con = get_db()
    cursor = await con.execute('SELECT course_id FROM blocks WHERE block_start=?', current_date)
    rows = await cursor.fetchall()
    return [row[0] for row in rows] if rows else []


async def update_lives_with_new_block(course_id):
    con = get_db()
    await con.execute('UPDATE users SET lives = ? WHERE course_id = ? AND lives != ?', (3, course_id, 0))
    await con.execute('''
               DELETE FROM history_of_lives
               WHERE user_id IN (
                   SELECT user_id FROM users WHERE course_id = ?
               )''', (course_id,))
    await con.execute('INSERT INTO history_of_lives VALUES(?, ?, ?, ?)', ('all_users', None, 3, '+3'))
    await con.commit()