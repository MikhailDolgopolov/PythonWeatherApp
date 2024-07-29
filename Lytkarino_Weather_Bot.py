import logging
import re
import threading
import time

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application, ConversationHandler, filters, MessageHandler

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from ForecastRendering import get_and_render, render_forecast_data
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

async def ensure_freshness(offset:int, telegram:Update) -> dict[str, str | Day]:
    data_to_send = {}
    if MetadataController.update_is_overdue(Day(offset)):
        await telegram.message.reply_text("Подождите, нужно получить актуальные данные...")
        new_data = fetch_forecast_thread(offset)
        await telegram.message.reply_text("Рисуем график...")
        data_to_send = render_forecast_data(new_data)
        return data_to_send

    data_to_send = get_and_render(offset)
    if MetadataController.update_is_due(Day(offset)):
        threading.Thread(target=fetch_forecast_thread, args=(offset,)).start()
    return data_to_send



def fetch_forecast_thread(day_number) -> ForecastData:
    print("Запрашиваю новые данные")
    forecast = Forecast()
    day = Day(day_number)
    return ForecastData(forecast, day)


async def tod(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    pic = await ensure_freshness(TODAY, update)

    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"])
    await update.message.reply_text(MetadataController.get_last_update(pic["day"]).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"))



async def send_today(update: Update, context: CallbackContext) -> int:
    await tod(update, context)
    return ConversationHandler.END


async def tom(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    pic = await ensure_freshness(TOMORROW, update)
    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"])
    await update.message.reply_text(MetadataController.get_last_update(pic["day"]).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"))


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
