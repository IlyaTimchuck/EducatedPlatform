import asyncio
import random
import logging

from google.oauth2.service_account import Credentials
import gspread_asyncio
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from gspread.utils import rowcol_to_a1

from app.bot.bot_instance import bot
import app.bot.infrastructure.database as db
import app.bot.keyboards as kb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GoogleSheetsClient:
    def __init__(
            self,
            creds_file: str,
            spreadsheet_id: str,
            max_retries: int = 2,
            notify_chat_id: int = 795508218,
    ) -> None:
        self._agcm = None
        self.spreadsheet = None
        self._creds_file = creds_file
        self.spreadsheet_id = spreadsheet_id
        self._last_modified_time = None
        self._max_retries = max_retries
        self.notify_chat_id = notify_chat_id

    async def _reinitialize(self) -> None:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        for attempt in range(1, self._max_retries + 1):
            try:
                creds = Credentials.from_service_account_file(
                    self._creds_file,
                    scopes=SCOPES,
                )
                self._agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)
                ags = await self._agcm.authorize()
                self.spreadsheet = await ags.open_by_key(self.spreadsheet_id)
                return
            except Exception as e:
                msg = f"Attempt {attempt}/{self._max_retries} to authorize Google Sheets failed: {e}"
                logger.warning(msg)
                await bot.send_message(chat_id=self.notify_chat_id, text=msg)
                await asyncio.sleep(1)
        self.spreadsheet = None

    async def _ensure_authorized(self, fn_name: str) -> None:
        if self.spreadsheet is None:
            await self._reinitialize()
        if self.spreadsheet is None:
            await bot.send_message(
                chat_id=self.notify_chat_id,
                text=f"Authorization error in {fn_name}",
            )

    async def _init_drive_service(self):
        scopes = ['https://www.googleapis.com/auth/drive']

        def build_service():
            creds = Credentials.from_service_account_file(
                self._creds_file,
                scopes=scopes,
            )
            return build('drive', 'v3', credentials=creds)

        return await asyncio.to_thread(build_service)

    async def get_exercise(self) -> list[str]:
        await self._ensure_authorized('get_exercise')
        ws = await self.spreadsheet.worksheet('add_task')
        exercises = await ws.get_all_values()
        await ws.delete_rows(2, len(exercises))
        return exercises[1:]

    async def add_user_in_table(self, real_name: str, telegram_username: str, course_title: str, user_id: int,
                                timezone: str, date_of_joining: str, role: str, lives: int) -> None:
        await self._ensure_authorized('add_user_in_table')
        ws = await self.spreadsheet.worksheet('users')
        row = [real_name, telegram_username, course_title, str(user_id), timezone, date_of_joining,
               role, 'active', f'{lives}❤️', '-', ]
        await ws.append_row(row)

    async def add_deadlines_in_table(self, data: list[list]) -> None:
        await self._ensure_authorized('add_deadlines_in_table')
        ws = await self.spreadsheet.worksheet('deadlines')
        await ws.append_rows(data, value_input_option='USER_ENTERED')

    async def add_course_in_table(self, course_data: list):
        await self._ensure_authorized('add_course_in_table')
        ws = await self.spreadsheet.worksheet('courses')
        await ws.append_row(course_data)

    async def check_for_updates(self) -> bool:
        await self._ensure_authorized('check_for_updates')
        drive = await self._init_drive_service()
        metadata = await asyncio.to_thread(
            lambda: drive.files()
            .get(fileId=self.spreadsheet_id, fields='modifiedTime')
            .execute()
        )
        modified = metadata.get('modifiedTime')
        logger.debug(f"Fetched modifiedTime: {modified}")
        if self._last_modified_time is None or modified != self._last_modified_time:
            self._last_modified_time = modified
            return True
        return False

    async def batch_set_lives_for_users(self, updates: list[tuple[int, int]]) -> None:
        await self._ensure_authorized('batch_set_lives_for_users')

        worksheet = await self.spreadsheet.worksheet('users')
        all_values = await worksheet.get_all_values()

        headers = [h.strip().lower() for h in all_values[0]]
        col_user_id = headers.index('user_id') + 1
        col_lives = headers.index('lives') + 1

        id_to_row = {
            row[col_user_id - 1]: idx
            for idx, row in enumerate(all_values[1:], start=2)
        }

        batch_data = []
        for user_id, new_lives in updates:
            row_num = id_to_row.get(str(user_id))
            if not row_num:
                continue
            cell_a1 = rowcol_to_a1(row_num, col_lives)
            batch_data.append({
                'range': cell_a1,
                'values': [[f'{new_lives}❤️']],
            })

        if batch_data:
            await worksheet.batch_update(
                batch_data,
                value_input_option='USER_ENTERED'
            )


async def setup_google_polling_loop(google_sheets_client: GoogleSheetsClient) -> None:
    await google_sheets_client.check_for_updates()

    while True:
        try:
            if await google_sheets_client.check_for_updates():
                logger.info("Detected update in Google Sheet")

                # --- ОБРАБОТКА ПОЛЬЗОВАТЕЛЕЙ ---
                ws_users = await google_sheets_client.spreadsheet.worksheet('users')
                raw_users = await ws_users.get_all_values()
                headers_users, users_rows = raw_users[0], raw_users[1:]
                normalized_users = [h.strip().lower() for h in headers_users]

                for i, row in enumerate(users_rows, start=2):
                    row_dict = dict(zip(normalized_users, row))
                    try:
                        status = row_dict.get('status', '').strip().lower()
                        update_time = row_dict.get('update_time', '-').strip()
                        uid = int(row_dict.get('user_id', '0'))

                        # 1) удаление пользователя
                        if status == 'deactivate':
                            username = row_dict.get('telegram_username', '')
                            await ws_users.delete_rows(i)
                            await bot.send_message(
                                chat_id=google_sheets_client.notify_chat_id,
                                text=(
                                    f"Вы действительно хотите удалить пользователя @{username} "
                                    f"и все его данные?"
                                ),
                                reply_markup=await kb.admin_keyboards.manage_students.confirm_deleting_user(uid)
                            )

                        # 2) изменение жизней
                        elif update_time != '-':
                            lives_str = row_dict.get('lives', '0').strip()
                            new_lives = int(lives_str[0]) if lives_str and lives_str[0].isdigit() else 0
                            logger.info(f"Updating lives for user {uid}: {new_lives}")
                            await db.deadlines.update_lives_for_user(uid, new_lives)
                            col_lives = normalized_users.index('lives') + 1
                            await ws_users.update_cell(i, col_lives, f'{new_lives}❤️')
                            col_upd = normalized_users.index('update_time') + 1
                            await ws_users.update_cell(i, col_upd, '-')

                    except Exception as e:
                        logger.error(f"Error processing users row {i}: {e}")
                        continue

                # --- ОБРАБОТКА ДЕДЛАЙНОВ ---
                ws_dead = await google_sheets_client.spreadsheet.worksheet('deadlines')
                raw_dead = await ws_dead.get_all_values()
                headers_dead, dead_rows = raw_dead[0], raw_dead[1:]
                normalized_dead = [h.strip().lower() for h in headers_dead]

                for j, row in enumerate(dead_rows, start=2):
                    row_dict = dict(zip(normalized_dead, row))
                    try:
                        update_time = row_dict.get('update_time', '-').strip()
                        uid_str = row_dict.get('user_id', '').strip()
                        tid_str = row_dict.get('task_id', '').strip()

                        if update_time != '-' and uid_str.isdigit() and tid_str.isdigit():
                            uid = int(uid_str)
                            tid = int(tid_str)
                            deadline = row_dict.get('deadline', '').strip()

                            logger.info(f"Updating deadline for {uid}, task {tid}: {deadline}")
                            await db.deadlines.change_deadline(uid, tid, deadline)
                            col_upd = normalized_dead.index('update_time') + 1
                            await ws_dead.update_cell(j, col_upd, '-')

                    except Exception as e:
                        logger.error(f"Error processing deadlines row {j}: {e}")
                        continue
                # --- ОБРАБОТКА КУРСОВ ---
                ws_courses = await google_sheets_client.spreadsheet.worksheet('courses')
                raw_courses = await ws_courses.get_all_values()
                headers_courses, courses_rows = raw_courses[0], raw_courses[1:]
                normalized_courses = [h.strip().lower() for h in headers_courses]

                for idx, row in enumerate(courses_rows, start=2):
                    row_dict = dict(zip(normalized_courses, row))
                    update_time = row_dict.get('update_time', '-').strip()
                    if update_time != '-':
                        new_course_name = row_dict.get('course_name')
                        course_id = row_dict.get('course_id')
                        await db.courses.change_course_name(new_course_name, int(course_id))
                        col_upd = normalized_courses.index('update_time') + 1
                        await ws_courses.update_cell(idx, col_upd, '-')
                        await asyncio.sleep(60 + random.randint(0, 5))

        except HttpError as http_err:
            logger.exception("Google API HttpError")
            await bot.send_message(
                chat_id=google_sheets_client.notify_chat_id,
                text=f"Google API error: {http_err}"
            )
            await asyncio.sleep(60)

        except Exception as e:
            logger.exception("Unhandled error in polling loop")
            await bot.send_message(
                chat_id=google_sheets_client.notify_chat_id,
                text=f"Error in google_polling_loop: {e}"
            )
            await asyncio.sleep(60)


google_client = GoogleSheetsClient(
    creds_file='educatedplatform-a40aded26c1c.json',
    spreadsheet_id='1dRVN0o5TVgZ7zfcPZOej8VCq508xeWfNhPLexWTINWE'
)
