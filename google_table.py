from google.oauth2.service_account import Credentials
import gspread_asyncio
from bot_instance import bot
import asyncio
import database as db


class GoogleSheetsClient:
    def __init__(self, creds_file, spreadsheet_id) -> None:
        self._agcm = None
        self._spreadsheet = None
        self._creds_file = creds_file
        self._spreadsheet_id = spreadsheet_id
        self._max_retries = 2

    async def _reinitialize(self) -> None:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        for attempt in range(1, self._max_retries + 1):
            try:
                creds = Credentials.from_service_account_file(self._creds_file, scopes=SCOPES)
                self._agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: creds)
                ags = await self._agcm.authorize()
                self._spreadsheet = await ags.open_by_key(self._spreadsheet_id)
                return
            except Exception as e:
                await bot.send_message(chat_id=795508218,
                                       text=f'{attempt} попытка авторизации google_sheets не была выполнена. Ошибка: {e}')
                print(f'Ошибка авторизации {e}')
                await asyncio.sleep(1)
        self._spreadsheet = None

    async def _ensure_authorized(self, function_name) -> None:
        if self._spreadsheet is None:
            await self._reinitialize()
        if self._spreadsheet is None:
            await bot.send_message(chat_id=795508218,
                                   text=f'При выполнении функции {function_name} произошла ошибка авторизации')

    async def get_exersice(self) -> list | str:
        await self._ensure_authorized('get_exercise')
        worksheet = await self._spreadsheet.get_worksheet(0)
        data = await worksheet.get_all_values()
        return data[1:]

    async def add_user_in_table(self, username: str, course_title: str, user_id: int, timezone: str,
                                date_of_joining: str, role: str, lives: int) -> None:
        await self._ensure_authorized('add_user_in_table')
        worksheet = await self._spreadsheet.worksheet('users')
        row_data = [username, course_title, user_id, timezone,
                                date_of_joining, role, f'{lives}❤️']
        await worksheet.append_row(row_data)


google_client = GoogleSheetsClient(creds_file='educatedplatform-8219d1d704e8.json',
                                   spreadsheet_id='1dRVN0o5TVgZ7zfcPZOej8VCq508xeWfNhPLexWTINWE')

# def get_creds():
#     SERVICE_ACCOUNT_FILE = "educatedplatform-8219d1d704e8.json"
#     SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
#     return Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#
#
# agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
#
#
# async def get_spreadsheet():
#     agc = await agcm.authorize()
#     spreadsheet = await agc.open_by_key("1dRVN0o5TVgZ7zfcPZOej8VCq508xeWfNhPLexWTINWE")  # замените на ваш ID таблицы
#     return spreadsheet
#
#
# async def get_exersice() -> list | str:
#     try:
#
#         worksheet = await spreadsheet.get_worksheet(0)
#         return worksheet[1:]
#     except Exception as e:
#         print(e)
#         return 'Ошибка на стороне Google, попробуй еще раз'
#
# def add_user_in_sheets(username, user_id, course_id, timezone_id, date_of_joining) -> None:
#     lives = 3
#     course_title = await db.
