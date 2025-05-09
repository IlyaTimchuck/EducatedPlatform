from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.environ['BOT_TOKEN']
GOOGLE_SHEETS_CREDS_FILE = os.environ['GOOGLE_SHEETS_CREDS_FILE']
GOOGLE_SPREADSHEET_ID = os.environ['GOOGLE_SPREADSHEET_ID']
ADMIN_USER_ID = int(os.environ['ADMIN_USER_ID'])