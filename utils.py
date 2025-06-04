import os
import re
from google_api import upload_file_to_drive, append_to_sheet
from telegram import Update
from telegram.ext import ContextTypes
import tempfile
from pdfminer.high_level import extract_text

# Сопоставление ФИО → объект (пример)
PERSON_TO_PROJECT = {
    "shatsila siarhei": "Tomaszewski Group (AACHEN)",
    "palubenski ivan": "INGOLSTADT",
    "yauhen siarhei": "INGOLSTADT",
    "rubtsevich pavel": "Frankfurt Lüftung (COLT)",
    "navichenka mikita": "Frankfurt Lüftung (COLT)",
    "nakladovich andrei": "Frankfurt Lüftung (COLT)",
    "tkach sergey": "PWConstruction Hamburg (Pavel)",
    "lisicinas vadimas": "PWConstruction Hamburg (Pavel)",
    "horbatiuk vasyl": "PWConstruction Hamburg (Pavel)",
    "tarasenco serghei": "PWConstruction Hamburg (Pavel)",
    "lewandowski marek": "PWConstruction Hamburg (Pavel)",
    # ... все остальные из твоего списка будут добавлены сюда
}

def extract_amount(text):
    match = re.search(r"(?:Total price[:\s]*EUR|EUR)\s*(\d+[.,]\d{2})", text, re.IGNORECASE)
    return float(match.group(1).replace(",", ".")) if match else 0.0

def extract_names(text):
    matches = re.findall(r"\b([A-Z][a-z]+\s[A-Z][a-z]+)\b", text)
    blocked = {"Manage", "Direction", "Luggage", "Stra", "Terms", "General", "Hold"}
    return list({m for m in matches if all(b not in m for b in blocked)})

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
        total = extract_amount(text)
        names = extract_names(text)
        count = max(len(names), 1)
        per_person = round(total / count, 2)

        for name in names:
            norm = name.lower().strip()
            project = PERSON_TO_PROJECT.get(norm, "")
            row = {
                "Дата": update.message.date.strftime("%d.%m.%Y"),
                "Объект": project,
                "Сотрудник": name,
                "Категория": "Билеты",
                "Сумма (€)": per_person,
                "Комментарий": "",
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
