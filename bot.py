import os
import logging
import traceback
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, CommandHandler, filters
from google_api import append_to_sheet, upload_file_to_drive
from utils import process_voice, extract_file_info
import datetime

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://expense-bot-ful9.onrender.com/webhook"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот готов. Отправьте сообщение, фото, PDF или голос.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg_date = datetime.datetime.now().strftime("%d.%m.%Y")
        data = {
            "Дата": msg_date,
            "Объект": "",
            "Категория": "",
            "Сумма": "",
            "Комментарий": "",
            "Тип": "текст",
            "Ссылка на файл": ""
        }

        if update.message.voice:
            data["Тип"] = "аудио"
            text = await process_voice(update, context)
            data["Комментарий"] = text
        elif update.message.document:
            data["Тип"] = "pdf"
            file_info = await extract_file_info(update, context)
            data["Ссылка на файл"] = file_info["url"]
            data["Комментарий"] = file_info["name"]
        elif update.message.photo:
            data["Тип"] = "фото"
            file_info = await extract_file_info(update, context, photo=True)
            data["Ссылка на файл"] = file_info["url"]
            data["Комментарий"] = file_info["name"]
        elif update.message.text:
            data["Комментарий"] = update.message.text

        append_to_sheet(data)
        await update.message.reply_text("✅ Сохранено.")
    except Exception as e:
        err = traceback.format_exc()
        await update.message.reply_text(f"❌ Ошибка при обработке:\n{err}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )