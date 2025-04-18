from google.oauth2.service_account import Credentials
import gspread_asyncio
from googleapiclient.discovery import build
from bot_instance import bot
import asyncio
import database as db
import keyboard as kb


class GoogleSheetsClient:
    def __init__(self, creds_file, spreadsheet_id) -> None:
        self._agcm = None
        self.spreadsheet = None
        self._drive_service = None
        self._last_modified_time = None
        self._creds_file = creds_file
        self.spreadsheet_id = spreadsheet_id
        self._max_retries = 2

    async def _reinitialize(self) -> None:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        for attempt in range(1, self._max_retries + 1):
            try:
                creds = Credentials.from_service_account_file(self._creds_file, scopes=SCOPES)
                self._agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)
                ags = await self._agcm.authorize()
                self.spreadsheet = await ags.open_by_key(self.spreadsheet_id)
                return
            except Exception as e:
                await bot.send_message(chat_id=795508218,
                                       text=f'{attempt} попытка авторизации google_sheets не была выполнена. Ошибка: {e}')
                print(f'Ошибка авторизации {e}')
                await asyncio.sleep(1)
        self.spreadsheet = None

    async def _ensure_authorized(self, function_name) -> None:
        if self.spreadsheet is None:
            await self._reinitialize()
        if self.spreadsheet is None:
            await bot.send_message(chat_id=795508218,
                                   text=f'При выполнении функции {function_name} произошла ошибка авторизации')

    async def _init_drive_service(self):
        scopes = ['https://www.googleapis.com/auth/drive']

        def build_service():
            creds = Credentials.from_service_account_file(self._creds_file, scopes=scopes)
            return build('drive', 'v3', credentials=creds)

        drive_service = await asyncio.to_thread(build_service)
        return drive_service

    async def get_exersice(self) -> list | str:
        await self._ensure_authorized('get_exercise')
        worksheet = await self.spreadsheet.get_worksheet(0)
        data = await worksheet.get_all_values()
        return data[1:]

    async def add_user_in_table(self, real_name: str, telegram_username: str, course_title: str, user_id: int,
                                timezone: str,
                                date_of_joining: str, role: str, lives: int) -> None:
        await self._ensure_authorized('add_user_in_table')
        worksheet = await self.spreadsheet.worksheet('users')
        status = 'active'
        row_data = [real_name, telegram_username, course_title, str(user_id), timezone,
                    date_of_joining, role, status, f'{lives}❤️', '-']
        await worksheet.append_row(row_data)

    async def check_for_updates(self):
        await self._ensure_authorized('check_for_updates')
        drive_service = await self._init_drive_service()

        file_metadata = await asyncio.to_thread(
            lambda: drive_service.files().get(
                fileId=self.spreadsheet_id,
                fields='modifiedTime'
            ).execute()
        )
        modified_time = file_metadata['modifiedTime']
        print(f"Время последнего изменения: {file_metadata.get('modifiedTime')}")
        if self._last_modified_time is None:
            self._last_modified_time = modified_time
            return True

        if modified_time != self._last_modified_time:
            self._last_modified_time = modified_time
            return True

        return False


google_client = GoogleSheetsClient(creds_file='educatedplatform-a40aded26c1c.json',
                                   spreadsheet_id='1dRVN0o5TVgZ7zfcPZOej8VCq508xeWfNhPLexWTINWE')


async def setup_google_polling_loop(google_sheets_client: GoogleSheetsClient):
    await google_sheets_client.check_for_updates()
    while True:
        try:
            has_updates = await google_sheets_client.check_for_updates()
            if has_updates:
                print('Произошло обновление таблицы')
                worksheet = await google_sheets_client.spreadsheet.worksheet('users')
                data = (await worksheet.get_all_values())[1:]
                for num_row, row_data in enumerate(data, 2):
                    print(row_data)
                    if row_data[-3] == 'deleted':
                        username = row_data[1]
                        user_id = row_data[3]
                        await worksheet.delete_rows(num_row)
                        await bot.send_message(chat_id=795508218,
                                               text=f'Вы действительно хотите удалить пользователя @{username} и все связанные с ним данные?',
                                               reply_markup=await kb.confirm_deleting_user(user_id))
                    elif row_data[-1] != '-':
                        user_id = int(row_data[3])
                        new_lives_count = int(row_data[8][0])
                        await db.update_lives_for_user(user_id, new_lives_count)
                        await worksheet.update_cell(row=num_row, col=10, value='-')

            await asyncio.sleep(60)
        except Exception as e:
            print(e)
            await bot.send_message(chat_id=795508218,
                                   text=f'В мониторинге google_polling_loop произошла ошибка: {e}')
            await asyncio.sleep(60)
