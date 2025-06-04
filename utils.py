import os
import re
from google_api import upload_file_to_drive, append_to_sheet
from telegram import Update
from telegram.ext import ContextTypes
import tempfile
from pdfminer.high_level import extract_text

async def process_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return "[голос не используется]"

# Сопоставление сотрудник → объект
PERSON_TO_PROJECT = {
    "shatila siarhei": "Tomaszewski Group (AACHEN)"
}

def normalize_name(name):
    return name.lower().strip()

def extract_amount(text):
    match = re.search(r"(?:EUR\s*)?(\d+[.,]\d{2})(?:\s*EUR)?", text, re.IGNORECASE)
    return float(match.group(1).replace(",", ".")) if match else 0.0

def extract_names(text):
    blocked = {"Manage", "Direction", "Luggage", "Stra", "Terms", "General", "Hold", "Company", "Seat"}
    matches = re.findall(r"\b([A-Z][a-z]+\s[A-Z][a-z]+)\b", text)
    return list({m for m in matches if all(b not in m for b in blocked)})

def extract_route(text):
    match = re.search(r"(Frankfurt|Klaipėda|Warsaw|Kaunas|Vilnius)[^\n]+?(→|\-\>|\sto\s)[^\n]+", text, re.IGNORECASE)
    return match.group(0).replace("->", "→") if match else ""

def extract_date(text):
    match = re.search(r"(\d{2}[./-]\d{2}[./-]\d{4})", text)
    return match.group(1).replace("/", ".").replace("-", ".") if match else ""

def extract_text_from_pdf(path):
    return extract_text(path)

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
        names = extract_names(text)
        total = extract_amount(text)
        route = extract_route(text)
        trip_date = extract_date(text)

        count = max(len(names), 1)
        per_person = round(total / count, 2)

        for name in names:
            norm = normalize_name(name)
            project = PERSON_TO_PROJECT.get(norm, "")
            row = {
                "Дата": trip_date,
                "Объект": project,
                "Сотрудник": name,
                "Категория": "Билеты",
                "Сумма (€)": per_person,
                "Комментарий": f"FlixBus {route}" if route else "",
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

    return {
        "url": file_url,
        "name": filename,
        "amount": "",
        "person": ""
    }
