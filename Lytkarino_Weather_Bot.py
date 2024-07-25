import logging
from telegram import Bot, Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, Application, ConversationHandler, ContextTypes, \
    CallbackQueryHandler

from helpers import read_json

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Telegram bot API token
TOKEN = read_json("secrets.json")["telegram_token"]

logger = logging.getLogger(__name__)

options = {}


# noinspection PyUnusedLocal
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello!')
    await update.message.reply_text("Available commands are: /start, /pic, /settings")


# noinspection PyUnusedLocal
async def settings(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data='set_option_1')],
        [InlineKeyboardButton("Option 2", callback_data='set_option_2')],
        [InlineKeyboardButton("Option 3", callback_data='set_option_3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)


# noinspection PyUnusedLocal
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # Update user settings based on the button pressed
    if data == 'set_option_1':
        options[user_id] = 'Option 1'
    elif data == 'set_option_2':
        options[user_id] = 'Option 2'
    elif data == 'set_option_3':
        options[user_id] = 'Option 3'

    await query.edit_message_text(text=f'Setting updated to: {options[user_id]}')


async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    pic = "D:/Programming/python/WeatherApp/Images/20240725-0-fgo.png"
    print("sending")
    await context.bot.send_photo(chat_id=chat_id, photo=pic)


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pic", send_image))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
