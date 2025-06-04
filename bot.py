import logging
import os
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from utils import process_ticket_file
from google_utils import extract_file_info, process_voice

# Установи свой токен и ID таблицы
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text("Привет! Отправь файл PDF или голосовое сообщение.")

def handle_file(update, context):
    file = update.message.document or update.message.photo[-1]
    if not file:
        return

    file_path = file.get_file().download()
    logger.info(f"Получен файл: {file_path}")
    if file.file_path.endswith(".pdf"):
        result = process_ticket_file(file_path, SPREADSHEET_ID)
        update.message.reply_text("Файл обработан и добавлен в таблицу." if result else "Ошибка при обработке PDF.")
    else:
        update.message.reply_text("Поддерживаются только PDF файлы.")

def handle_voice(update, context):
    voice = update.message.voice
    if not voice:
        return

    voice_file = voice.get_file().download()
    logger.info(f"Получено голосовое сообщение: {voice_file}")
    result = process_voice(voice_file, SPREADSHEET_ID)
    update.message.reply_text("Голосовое сообщение обработано." if result else "Ошибка при обработке голосового.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_file))
    dp.add_handler(MessageHandler(Filters.voice, handle_voice))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
