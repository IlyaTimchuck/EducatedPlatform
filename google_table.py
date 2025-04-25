import asyncio
import random
import logging

from google.oauth2.service_account import Credentials
import gspread_asyncio
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bot_instance import bot
import database as db
import keyboard as kb

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

    async def _ensure_authorized(self, function_name: str) -> None:
        if self.spreadsheet is None:
            await self._reinitialize()
        if self.spreadsheet is None:
            await bot.send_message(
                chat_id=self.notify_chat_id,
                text=f"Authorization error in {function_name}",
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
        worksheet = await self.spreadsheet.get_worksheet(0)
        data = await worksheet.get_all_values()
        return data[1:]

    async def add_user_in_table(
            self,
            real_name: str,
            telegram_username: str,
            course_title: str,
            user_id: int,
            timezone: str,
            date_of_joining: str,
            role: str,
            lifes: int,
    ) -> None:
        await self._ensure_authorized('add_user_in_table')
        worksheet = await self.spreadsheet.worksheet('users')
        status = 'active'
        row_data = [
            real_name,
            telegram_username,
            course_title,
            str(user_id),
            timezone,
            date_of_joining,
            role,
            status,
            f'{lifes}❤️',
            '-'
        ]
        await worksheet.append_row(row_data)

    async def add_deadlines_in_table(self, data: list[list]) -> None:
        await self._ensure_authorized('add_deadlines_in_table')
        worksheet = await self.spreadsheet.worksheet('deadlines')
        await worksheet.append_rows(data)

    async def check_for_updates(self) -> bool:
        await self._ensure_authorized('check_for_updates')
        drive_service = await self._init_drive_service()

        metadata = await asyncio.to_thread(
            lambda: drive_service.files()
            .get(fileId=self.spreadsheet_id, fields='modifiedTime')
            .execute()
        )
        modified_time = metadata.get('modifiedTime')
        logger.debug(f"Fetched modifiedTime: {modified_time}")

        if self._last_modified_time is None or modified_time != self._last_modified_time:
            self._last_modified_time = modified_time
            return True
        return False

google_client = GoogleSheetsClient(creds_file='educatedplatform-a40aded26c1c.json',
                                   spreadsheet_id='1dRVN0o5TVgZ7zfcPZOej8VCq508xeWfNhPLexWTINWE')



async def setup_google_polling_loop(google_sheets_client: GoogleSheetsClient) -> None:
    await google_sheets_client.check_for_updates()
    while True:
        try:
            if await google_sheets_client.check_for_updates():
                logger.info("Произошло обновление таблицы")

                ws_users = await google_sheets_client.spreadsheet.worksheet('users')
                raw_users = await ws_users.get_all_values()
                headers_users, users_rows = raw_users[0], raw_users[1:]
                lifes_data = []

                for row_idx, row in enumerate(users_rows, start=2):
                    row_dict = dict(zip(headers_users, row))
                    try:
                        status = row_dict.get('Status', '').strip().lower()
                        update_time = row_dict.get('Update_time', '-').strip()
                        uid_str = row_dict.get('User_id', '').strip()

                        if not uid_str.isdigit():
                            raise ValueError("Invalid User_id")
                        user_id = int(uid_str)

                        if status == 'deactivate':
                            username = row_dict.get('Telegram_username')
                            await ws_users.delete_rows(row_idx)
                            await bot.send_message(
                                chat_id=google_sheets_client.notify_chat_id,
                                text=(
                                    f"Вы действительно хотите удалить пользователя "
                                    f"@{username} и все связанные с ним данные?"
                                ),
                                reply_markup=await kb.confirm_deleting_user(user_id)
                            )

                        elif update_time != '-':
                            lifes_str = row_dict.get('lifes', '').strip()
                            new_lifes = int(lifes_str[0]) if lifes_str and lifes_str[0].isdigit() else 0
                            lifes_data.append((user_id, new_lifes))
                            upd_col = headers_users.index('Update_time') + 1
                            await ws_users.update_cell(row_idx, upd_col, '-')

                    except Exception as e:
                        logger.error(f"Parsing users error row {row_idx}: {e}")
                        continue

                ws_dead = await google_sheets_client.spreadsheet.worksheet('deadlines')
                raw_dead = await ws_dead.get_all_values()
                headers_dead, dead_rows = raw_dead[0], raw_dead[1:]
                deadlines_data = []

                for row_idx, row in enumerate(dead_rows, start=2):
                    row_dict = dict(zip(headers_dead, row))
                    try:
                        update_time = row_dict.get('Update_time', '-').strip()
                        uid_str = row_dict.get('User_id', '').strip()
                        tid_str = row_dict.get('Task_id', '').strip()

                        if update_time != '-' and uid_str.isdigit() and tid_str.isdigit():
                            user_id = int(uid_str)
                            task_id = int(tid_str)
                            deadline = row_dict.get('Deadline', '').strip()
                            deadlines_data.append((user_id, task_id, deadline))
                            upd_col = headers_dead.index('Update_time') + 1
                            await ws_dead.update_cell(row_idx, upd_col, '-')

                    except Exception as e:
                        logger.error(f"Parsing deadlines error row {row_idx}: {e}")
                        continue

                if lifes_data:
                    logger.info(f"Updating lifes: {lifes_data}")
                    for user_id, new_lifes in lifes_data:
                        await db.update_lifes_for_user(user_id, new_lifes)

                if deadlines_data:
                    logger.info(f"Updating deadlines: {deadlines_data}")
                    for user_id, task_id, deadline in deadlines_data:
                        await db.change_deadline(user_id, task_id, deadline)

            await asyncio.sleep(60 + random.randint(0, 5))

        except HttpError as http_err:
            logger.exception("Google API HttpError")
            await bot.send_message(
                chat_id=google_sheets_client.notify_chat_id,
                text=f"Ошибка Google API: {http_err}"
            )
            await asyncio.sleep(60)

        except Exception as e:
            logger.exception("Unhandled error in polling loop")
            await bot.send_message(
                chat_id=google_sheets_client.notify_chat_id,
                text=f"В мониторинге google_polling_loop произошла ошибка: {e}"
            )
            await asyncio.sleep(60)
