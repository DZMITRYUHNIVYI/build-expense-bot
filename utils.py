import os
import re
from google_api import upload_file_to_drive
from telegram import Update
from telegram.ext import ContextTypes
import tempfile
import fitz  # PyMuPDF

async def process_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = await update.message.voice.get_file()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    await voice.download_to_drive(temp_file.name)
    return "[распознанный текст из аудио]"

def extract_amount(text):
    match = re.search(r"(\d+[.,]\d{2})", text)
    print("🔍 Поиск суммы. Найдено:", match.group(1) if match else "ничего")
    return match.group(1).replace(",", ".") if match else ""

def extract_name(text):
    match = re.search(r"([A-Z][a-z]+\s[A-Z][a-z]+)", text)
    print("🔍 Поиск имени. Найдено:", match.group(1) if match else "ничего")
    return match.group(1) if match else ""

def extract_text_from_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    print("📄 Извлечённый текст из PDF:", text[:300], "..." if len(text) > 300 else "")
    return text

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

    info = {
        "url": file_url,
        "name": filename,
        "amount": "",
        "person": ""
    }

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(temp_path)
        info["amount"] = extract_amount(text)
        info["person"] = extract_name(text)
