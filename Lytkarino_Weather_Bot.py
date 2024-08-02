from datetime import datetime, timedelta
import logging
import re
import threading
import time

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application, ConversationHandler, filters, MessageHandler

from Day import Day
from Forecast import Forecast
from ForecastRendering import render_forecast_data
from MetadataController import MetadataController
from helpers import read_json, delete_old_files

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Telegram bot API token
TOKEN = read_json("secrets.json")["telegram_token"]

logger = logging.getLogger(__name__)

TODAY, TOMORROW = range(2)

options = {"temps": None, "rains": None}


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет!')
    time.sleep(1)
    await update.message.reply_text(
        "Мне можно отправить любое сообщение со словами 'сегодня' или 'завтра', и я отправлю прогноз. Вот пример:")
    time.sleep(1)
    await context.bot.send_photo(chat_id=update.message.chat_id, photo="demo.png")
    time.sleep(2)
    await update.message.reply_text("""На графике показаны:
    - температура из трёх источников (Foreca.ru, Gismeteo.ru, Open-Meteo.com)
    - количество осадков в час
    - световой день
    """)


async def send(update: Update, context: CallbackContext, date: datetime):
    chat_id = update.message.chat_id
    forecast = Forecast(temp_sources=options["temps"], rainfall_sources=options["rains"])
    pic = render_forecast_data(forecast, date)

    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"], caption=forecast.last_updated(date).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"))




def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*завтра)сегодня(?!.*завтра).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today())))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*сегодня)завтра(?!.*сегодня).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today()+timedelta(days=1))))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
