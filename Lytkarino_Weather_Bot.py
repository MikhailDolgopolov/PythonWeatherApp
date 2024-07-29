import logging
import re
import threading
import time

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application, ConversationHandler, filters, MessageHandler

from Day import Day
from Forecast import Forecast
from ForecastRendering import get_and_render
from MetadataController import MetadataController
from helpers import read_json

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Telegram bot API token
TOKEN = read_json("secrets.json")["telegram_token"]

logger = logging.getLogger(__name__)

TODAY, TOMORROW = range(2)


# noinspection PyUnusedLocal
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет!')
    time.sleep(1)
    await update.message.reply_text(
        "Мне можно отправить любое сообщение со словами 'сегодня' или 'завтра', и я отправлю прогноз. Вот пример:")
    time.sleep(0.5)
    await context.bot.send_photo(chat_id=update.message.chat_id, photo="demo.png")
    time.sleep(2)
    await update.message.reply_text("""На графике показаны:
    - температура из трёх источников
    - средняя температура из тех же данных
    - количество осадков в час из трех источников
    - световой день
    Также, насыщенность цвета столбчатой диаграммы показывает, насколько совпадает количество осадков в разных источниках.""")


def fetch_forecast_thread(day_number):
    forecast = Forecast()
    day = Day(day_number)
    print("processing....")
    time.sleep(15)
    forecast.fetch_forecast(day)
    print("done all processing")


async def tod(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    pic = get_and_render(TODAY)

    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"])
    await update.message.reply_text(MetadataController.get_last_update(pic["day"]).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"))

    print("Checking update")
    threading.Thread(target=fetch_forecast_thread, args=(0,)).start()


async def send_today(update: Update, context: CallbackContext) -> int:
    await tod(update, context)
    return ConversationHandler.END


async def tom(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    pic = get_and_render(TOMORROW)
    print("sending tomorrow")
    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"])
    await update.message.reply_text(MetadataController.get_last_update(pic["day"]).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"))
    print("Checking update")
    threading.Thread(target=fetch_forecast_thread, args=(1,)).start()


async def send_tomorrow(update: Update, context: CallbackContext) -> int:
    await tom(update, context)
    return ConversationHandler.END


async def tt1(update: Update, context: CallbackContext) -> int:
    await tod(update, context)
    time.sleep(0.5)
    await tom(update, context)
    return ConversationHandler.END


async def tt2(update: Update, context: CallbackContext) -> int:
    await tom(update, context)
    time.sleep(0.5)
    await tod(update, context)
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", send_today))
    application.add_handler(CommandHandler("tomorrow", send_tomorrow))

    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*завтра)сегодня(?!.*завтра).*$', re.IGNORECASE)), send_today))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*сегодня)завтра(?!.*сегодня).*$', re.IGNORECASE)),
                       send_tomorrow))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'сегодня.*завтра', re.IGNORECASE)), tt1))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'завтра.*сегодня', re.IGNORECASE)), tt2))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
