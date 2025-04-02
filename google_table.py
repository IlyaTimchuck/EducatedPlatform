from google.oauth2.service_account import Credentials
import gspread
import database as db

def get_exersice() -> list|str:
    try:
        SERVICE_ACCOUNT_FILE = "educatedplatform-8219d1d704e8.json"
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)

        spreadsheet = gc.open_by_key("1dRVN0o5TVgZ7zfcPZOej8VCq508xeWfNhPLexWTINWE")
        worksheet = spreadsheet.sheet1

        data = worksheet.get_all_values()
        return data[1:]
    except Exception as e:
        print(e)
        return 'Ошибка на стороне Google, попробуй еще раз'


# def add_user_in_sheets(username, user_id, course_id, timezone_id, date_of_joining) -> None:
#     lives = 3
#     course_title = await db.