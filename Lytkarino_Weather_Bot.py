import logging
import re
from datetime import datetime
import time
from telegram import Bot, Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, Application, ConversationHandler, ContextTypes, \
    CallbackQueryHandler, filters, MessageHandler

from ForecastRendering import get_and_render
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
    await update.message.reply_text("Мне можно отправить любое сообщение со словами 'сегодня' или 'завтра', и я отправлю прогноз. Вот пример:")
    time.sleep(0.5)
    await context.bot.send_photo(chat_id=update.message.chat_id, photo="demo.png")
    time.sleep(2)
    await update.message.reply_text("""На графике показаны:
    - температура из трёх источников
    - средняя температура из тех же данных
    - среднее количество осадков в час
    - вероятность выпадения осадков, по OpenMeteo (ширина голубой полоски под столбчатой диаграммой)
    - световой день
    Также, насыщенность цвета столбчатой диаграммы показывает, насколько совпадает количество осадков в разных источниках.""")



async def tod(update: Update, context: CallbackContext):

    chat_id = update.message.chat_id
    pic = get_and_render(TODAY)

    print("sending today")
    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"])

    metadata = read_json("metadata.json")
    await update.message.reply_text(datetime.strptime(metadata[pic['day'].short_date], '%Y-%m-%dT%H:%M:%S').strftime(
        "Данные плучены %d.%m.%Y, в %H:%M"))
async def send_today(update: Update, context: CallbackContext) -> int:
    await tod(update, context)
    return ConversationHandler.END


async def tom(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    pic = get_and_render(TOMORROW)
    print("sending tomorrow")
    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"])
    metadata = read_json("metadata.json")
    print(metadata)
    await update.message.reply_text(datetime.strptime(metadata[pic['day'].short_date], '%Y-%m-%dT%H:%M:%S').strftime(
        "Данные плучены %d.%m.%Y, в %H:%M"))
async def send_tomorrow(update: Update, context: CallbackContext) -> int:
    await tom(update, context)
    return ConversationHandler.END


async def tt1(update: Update, context: CallbackContext) -> int:
    await tom(update, context)
    await tod(update, context)
    return ConversationHandler.END

async def tt2(update: Update, context: CallbackContext) -> int:
    await tod(update, context)
    await tom(update, context)
    return ConversationHandler.END

def main() -> None:

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", send_today))
    application.add_handler(CommandHandler("tomorrow", send_tomorrow))

    application.add_handler(MessageHandler(filters.Regex(re.compile(r'сегодня(?!.*завтра)', re.IGNORECASE)), send_today))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'завтра(?!.*сегодня)', re.IGNORECASE)), send_today))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'сегодня.*завтра', re.IGNORECASE)), tt1))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'завтра.*сегодня', re.IGNORECASE)), tt2))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
