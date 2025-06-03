import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS_JSON), scope)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

def append_to_sheet(data):
    try:
        row = [data.get("Дата"), data.get("Объект"), data.get("Категория"),
               data.get("Сумма"), data.get("Комментарий"), data.get("Тип"), data.get("Ссылка на файл")]
        print("📥 Добавление строки:", row)
        sheet.append_row(row)
    except Exception as e:
        print("❌ Ошибка при добавлении строки в Google Таблицу:", str(e))
        raise

def upload_file_to_drive(file_path, file_name):
    service = build("drive", "v3", credentials=credentials)
    file_metadata = {"name": file_name}
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return f"https://drive.google.com/file/d/{uploaded_file['id']}/view"
