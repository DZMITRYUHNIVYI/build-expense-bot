import re
import fitz  # PyMuPDF
import logging
from datetime import datetime
from google_utils import append_to_sheet, upload_file_to_drive

PERSON_TO_PROJECT = {
    "elnur musaev": "Проект1",
    "behbid behbidzade": "Проект1",
    "ibrahim aghaev": "Проект1"
}

logger = logging.getLogger(__name__)

def parse_pdf_ticket(pdf_path):
    with fitz.open(pdf_path) as doc:
        text = "\n".join(page.get_text() for page in doc)

    date = None
    m_date = re.search(r'(\d{2}[./-]\d{2}[./-]\d{4})', text)
    if m_date:
        try:
            date = datetime.strptime(m_date.group(1), "%d.%m.%Y").date()
        except ValueError:
            logger.error(f"Invalid date format: {m_date.group(1)}")

    names = []
    for line in text.splitlines():
        m = re.match(r"^([A-Z][a-z]+\s[A-Z][a-z]+)(\s+\d+|\s+·)?", line)
        if m:
            names.append(m.group(1).strip())

    names = list(set(names))

    total_price = None
    m_price = re.search(r'Total price[:\s]*EUR\s*([\d\.,]+)', text)
    if m_price:
        total_price = float(m_price.group(1).replace(',', '.'))

    route = None
    m_route = re.search(r'([A-Za-z]+)\s*(→|->|to)\s*([A-Za-z]+)', text)
    if m_route:
        route = f"{m_route.group(1)} → {m_route.group(3)}"

    return date, names, total_price, route

def process_ticket_file(pdf_path, spreadsheet_id):
    date, names, total_price, route = parse_pdf_ticket(pdf_path)
    if not names or total_price is None or date is None:
        logger.error(f"Skipping file {pdf_path}: missing data")
        return None

    drive_link = upload_file_to_drive(pdf_path)
    comment = f"FlixBus {route}" if route else "FlixBus"
    per_person = round(total_price / len(names), 2)

    for name in names:
        key = name.lower()
        project = PERSON_TO_PROJECT.get(key)
        if not project:
            logger.warning(f"No project for {name}")
            continue
        row = [
            date.strftime("%d.%m.%Y"),
            project,
            name,
            "Билеты",
            per_person,
            comment,
            "pdf",
            drive_link
        ]
        append_to_sheet(spreadsheet_id, row)
    return drive_link
