import aiosqlite

_db: aiosqlite.Connection | None = None


async def init_db(path: str) -> None:
    global _db
    _db = await aiosqlite.connect(path)
    await _db.execute("PRAGMA journal_mode=WAL;")
    await _db.execute("PRAGMA synchronous=NORMAL;")
    await _db.execute("DROP TABLE IF EXISTS unregistered")
    await _db.execute("DROP TABLE IF EXISTS users")
    await _db.execute("DROP TABLE IF EXISTS courses")
    await _db.execute("DROP TABLE IF EXISTS blocks")
    await _db.execute("DROP TABLE IF EXISTS tasks")
    await _db.execute("DROP TABLE IF EXISTS exercises")
    await _db.execute("DROP TABLE IF EXISTS learning_progress")
    await _db.execute("DROP TABLE IF EXISTS sessions")
    await _db.execute("DROP TABLE IF EXISTS changed_deadlines")
    await _db.execute("DROP TABLE IF EXISTS timezones")
    await _db.execute("DROP TABLE IF EXISTS history_of_lives")
    await _db.execute("DROP TABLE IF EXISTS session_files")
    await _db.execute("PRAGMA foreign_keys = ON;")
    await _db.execute("""CREATE TABLE IF NOT EXISTS courses (
                course_title TEXT,
                course_id INTEGER PRIMARY KEY AUTOINCREMENT
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS timezones (
                timezone TEXT,
                timezone_id INTEGER PRIMARY KEY AUTOINCREMENT
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS users (
                real_name TEXT,
                telegram_username TEXT,
                user_id INTEGER PRIMARY KEY,
                course_id INTEGER,
                timezone_id INTEGER,
                date_of_joining TEXT,
                lives INTEGER,
                role TEXT,
                FOREIGN KEY(course_id) REFERENCES courses(course_id),
                FOREIGN KEY(timezone_id) REFERENCES timezones(timezone_id)
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS unregistered (
                telegram_username TEXT,
                course_id INTEGER,
                FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS blocks (
                course_id INTEGER,
                block_number INTEGER,
                block_id INTEGER PRIMARY KEY AUTOINCREMENT,
                FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS tasks (
                task_title TEXT,
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_id INTEGER,
                file_work BOOL,
                video_id TEXT,
                abstract_id TEXT,
                link_files TEXT,
                deadline TEXT,
                FOREIGN KEY(block_id) REFERENCES blocks(block_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS exercises (
                task_id INTEGER,
                exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_condition TEXT,
                exercise_answer TEXT,
                FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id INTEGER,
                is_completed BOOL,
                session_start TEXT,
                session_end TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS learning_progress (
                user_id INTEGER,
                exercise_id INTEGER,
                input_answer TEXT,
                right_answer BOOL,
                session_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY(exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS changed_deadlines (
                user_id INTEGER,
                task_id INTEGER,
                deadline TEXT,
                PRIMARY KEY(user_id, task_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS history_of_lives (
                user_id INTEGER,
                task_id INTEGER,
                lives_after_action INTEGER,
                action TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TABLE IF NOT EXISTS session_files (
                session_id INTEGER PRIMARY KEY,
                file_work_id TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )""")
    await _db.execute("""CREATE TRIGGER IF NOT EXISTS delete_empty_course
                AFTER DELETE ON users
                BEGIN
                    DELETE FROM courses
                    WHERE course_id = OLD.course_id
                    AND NOT EXISTS (
                        SELECT 1 FROM users 
                        WHERE course_id = OLD.course_id
                        )
                    AND NOT EXISTS (
                        SELECT 1 FROM unregistered
                        WHERE course_id = OLD.course_id
                        );
                END""")
    await _db.execute("""CREATE TRIGGER IF NOT EXISTS delete_empty_timezone
                AFTER DELETE ON users
                BEGIN
                    DELETE FROM timezones
                    WHERE timezone_id = OLD.timezone_id
                    AND NOT EXISTS (
                        SELECT 1 FROM users WHERE timezone_id = OLD.timezone_id);
                END""")
    await _db.commit()

def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db