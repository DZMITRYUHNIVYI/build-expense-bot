import os
import re
from google_api import upload_file_to_drive, append_to_sheet
from telegram import Update
from telegram.ext import ContextTypes
import tempfile
from pdfminer.high_level import extract_text

async def process_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = await update.message.voice.get_file()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    await voice.download_to_drive(temp_file.name)
    return "[распознанный текст из аудио]"

def extract_amount(text):
    match = re.search(r"(?:Total price[:\s]*EUR|EUR)\s*(\d+[.,]\d{2})", text, re.IGNORECASE)
    return float(match.group(1).replace(",", ".")) if match else 0.0

def extract_names(text):
    matches = re.findall(r"([A-Z][a-z]+\s[A-Z][a-z]+)", text)
    return list(set(matches))

def extract_text_from_pdf(path):
    text = extract_text(path)
    print("📄 Извлечённый текст из PDF:", text[:500], "..." if len(text) > 500 else "")
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

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(temp_path)
        total = extract_amount(text)
        names = extract_names(text)
        print(f"✅ Найдено имён: {names}, сумма: {total}")

        count = max(len(names), 1)
        per_person = round(total / count, 2) if count else 0.0

        for name in names:
            row = {
                "Дата": update.message.date.strftime("%d.%m.%Y"),
                "Объект": "",
                "Категория": "Билеты",
                "Сумма": per_person,
                "Комментарий": name,
                "Тип": "pdf",
                "Ссылка на файл": file_url
            }
            append_to_sheet(row)

        return {
            "url": file_url,
            "name": filename,
            "amount": total,
            "person": ", ".join(names)
        }
    else:
        return {
            "url": file_url,
            "name": filename,
            "amount": "",
            "person": ""
        }
