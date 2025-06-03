import os
from google_api import upload_file_to_drive
from telegram import Update
from telegram.ext import ContextTypes
import tempfile
import aiofiles

async def process_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = await update.message.voice.get_file()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    await voice.download_to_drive(temp_file.name)
    # заглушка — тут можно подключить whisper или Google Speech API
    return "[распознанный текст из аудио]"

async def extract_file_info(update: Update, context: ContextTypes.DEFAULT_TYPE, photo=False):
    if photo:
        file = await update.message.photo[-1].get_file()
        filename = f"photo_{update.message.message_id}.jpg"
    else:
        file = await update.message.document.get_file()
        filename = update.message.document.file_name

    temp_path = f"/tmp/{filename}"
    await file.download_to_drive(temp_path)
    file_url = upload_file_to_drive(temp_path, filename)
    return {"url": file_url, "name": filename}