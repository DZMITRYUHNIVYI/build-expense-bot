import os
import re
from google_api import upload_file_to_drive, append_to_sheet
from telegram import Update
from telegram.ext import ContextTypes
import tempfile
from pdfminer.high_level import extract_text

async def process_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return "[голос не используется]"

PERSON_TO_PROJECT = {
    "hradouski andrei": "INGOLSTADT",
    "siarhei vaskevich": "INGOLSTADT",
    "siarhei peahko": "INGOLSTADT",
    "pavel vaitushka": "INGOLSTADT",
    "andrei padzialinski": "INGOLSTADT",
    "uladzimir astapchuk": "INGOLSTADT",
    "andrei palauchenia": "INGOLSTADT",
    "ilya zhuk": "INGOLSTADT",
    "siarhei khmurovich": "INGOLSTADT",
    "stsiatsko anton": "INGOLSTADT",
    "shatsila siarhei": "Tomaszewski Group (AACHEN)",
    "kuliakin andrei": "Tomaszewski Group (AACHEN)",
    "kazakevich siarhei": "Tomaszewski Group (AACHEN)",
    "biadniuk piotr": "Tomaszewski Group (AACHEN)",
    "markau aliaksandr": "Tomaszewski Group (AACHEN)",
    "nechayeu ihar": "HLS",
    "bychuk aleh": "HLS",
    "kunitski vitali": "HLS",
    "mikutksi valery": "HLS",
    "makarau mikhail": "HLS",
    "asipovich andrei": "HLS",
    "kalesnikau aliaksei": "HLS",
    "sinkevich yury": "HLS",
    "matsukevich mikita": "Frankfurt Lüftung (FRA33)",
    "mamedau andrei": "Frankfurt Lüftung (FRA33)",
    "stepchuk dzmytro": "Frankfurt Lüftung (FRA33)",
    "khvat artur": "Tomaszewski Group (Bochum)",
    "buinavets vasili": "Tomaszewski Group (Bochum)",
    "kazakevich vitali": "Tomaszewski Group (Bochum)",
    "zasutski maksim": "Tomaszewski Group (Bochum)",
    "sadouski dzmitry": "Tomaszewski Group (Bochum)",
    "khojiev bokhodir": "Tomaszewski Group (Bochum)",
    "pihaleu dzmitry": "Tomaszewski Group (Bochum)",
    "palamarchyk oleksandr": "Tomaszewski Group (Bochum)",
    "shutkevich pavial": "CAVERION (Dortmund)",
    "chudzilouski dzianis": "CAVERION (Dortmund)",
    "polak arkadiusz": "CAVERION (Dortmund)",
    "tkach sergey": "PWConstruction Hamburg (Pavel)",
    "lisicinas vadimas": "PWConstruction Hamburg (Pavel)",
    "horbatiuk vasyl": "PWConstruction Hamburg (Pavel)",
    "tarasenco serghei": "PWConstruction Hamburg (Pavel)",
    "lewandowski marek": "PWConstruction Hamburg (Pavel)",
    "rubtsevich pavel": "Frankfurt Lüftung (COLT)",
    "navichenka mikita": "Frankfurt Lüftung (COLT)",
    "nakladovich andrei": "Frankfurt Lüftung (COLT)",
    "kirkevich siarhei": "Виктор 3",
    "zharko ihar": "Виктор 3",
    "haurylchuk viktar": "Виктор 3",
    "amelka kiryl": "Виктор 3",
    "maroz maksim": "Виктор 3",
    "haurylchuk vlad": "Виктор 3",
    "sharipov anatolii": "Виктор 3",
    "kulak dzmitry": "Виктор 3",
    "khaletski pavel": "Виктор 3",
    "shchuka dzmitry": "Виктор 3",
    "luchko aleh": "Виктор 3",
    "yankouski dzmitry": "Виктор 3",
    "yutskevich mikhail": "Виктор 3",
    "vauchok stanislau": "Виктор 3",
    "hutsko yury": "Виктор 3",
    "vidlouski vitali": "Виктор 3",
    "sviarhun andrei": "Виктор 3",
    "siamionau siarhei": "REGENSBURG",
    "barysau siarhei": "REGENSBURG",
    "vereteyko aleksander": "REGENSBURG",
    "marozau maksim": "REGENSBURG",
    "prykhodzka yauhen": "REGENSBURG",
    "dziazmyncki mikalai": "REGENSBURG",
    "kaniashin ruslan": "REGENSBURG",
    "sevastsyan siarhei": "REGENSBURG",
    "dzewanouski uladzislau": "REGENSBURG",
    "zenchyk dzmitry": "REGENSBURG",
    "riazanov yevhenii": "REGENSBURG",
    "sadouski siarhei": "REGENSBURG",
    "zaleuski dzmitry": "REGENSBURG",
    "lisai siarhei": "REGENSBURG",
    "kalko dzmitry": "REGENSBURG",
    "auseichyk maksim": "REGENSBURG",
    "bolog sahos": "REGENSBURG",
    "varadi oleksandr": "REGENSBURG",
    "vasilchyk henadzi": "REGENSBURG",
    "golubev igor": "REGENSBURG",
    "tsybulski yury": "REGENSBURG",
    "biareshchanka ihar": "REGENSBURG",
    "vaseichyk vladislav": "REGENSBURG",
    "shmyhaliou andrei": "REGENSBURG",
    "saidashau viacheslau": "REGENSBURG",
    "baihot aleh": "REGENSBURG",
    "nerushau aliaksandr": "REGENSBURG",
    "malak robert": "REGENSBURG",
    "krasniatsou dzianis": "REGENSBURG",
    "kulishevich dzmitry": "REGENSBURG",
    "kadzevich maks": "REGENSBURG",
    "drabovich raman": "REGENSBURG"
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
