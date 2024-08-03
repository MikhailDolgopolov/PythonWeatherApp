import os
from datetime import datetime, timedelta, date
import logging
import re
import threading
import time
from pprint import pformat
from typing import Union

import numpy as np
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import (
    Application,
    PicklePersistence,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackContext, filters, CallbackQueryHandler)

from Day import Day
from Forecast import Forecast
from ForecastRendering import render_forecast_data
from helpers import read_json

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Telegram bot API token
TOKEN = read_json("secrets.json")["telegram_token"]

logger = logging.getLogger(__name__)

CHOOSING_SETTING, R_SETTINGS, T_SETTINGS, = 0, 1, 2
CHOOSING_DAY = 3
STOP_WORD = "Утвердить"

sites = Forecast.all_sources()


def source_keyboard():
    keyboard = [[InlineKeyboardButton(s, callback_data=s)] for s in sites]
    keyboard.append([InlineKeyboardButton(STOP_WORD, callback_data="stop")])
    return keyboard


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет!')
    time.sleep(1)
    await update.message.reply_text(
        "Мне можно отправить любое сообщение со словами 'сегодня' или 'завтра', и я отправлю прогноз. Вот пример:")
    time.sleep(1)
    await context.bot.send_photo(chat_id=update.message.chat_id, photo="demo.png")
    time.sleep(1)
    await update.message.reply_text("""На графике показаны:
    - температура из трёх источников (Foreca.ru, Gismeteo.ru, Open-Meteo.com)
    - количество осадков в час
    - световой день
    """)
    time.sleep(1)
    await update.message.reply_text(
        "Также, можно настроить, из данных каких сайтов будут показаны температура и осадки. Для этого используй команду /settings")
    context.chat_data.clear()
    context.chat_data["temp-sources"] = sites
    context.chat_data["rain-sources"] = sites


async def send(thing: Union[Update, CallbackQuery], context: CallbackContext, date: datetime) -> int:
    chat_id = thing.message.chat_id
    initial_message = await thing.message.reply_text('Это может занять некоторое время...')
    t, r = context.chat_data.get("temp-sources", []), context.chat_data.get("rain-sources", [])
    forecast = Forecast(temp_sources=t, rainfall_sources=r)
    pic = render_forecast_data(forecast, date, uid=chat_id)

    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"], caption=forecast.last_updated(date).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"))
    await initial_message.delete()
    os.remove(pic["path"])

    keyboard = [[InlineKeyboardButton("Выбрать снова", callback_data="again")]]
    time.sleep(1)
    await thing.message.reply_text("Нужно?", reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSING_DAY



def current_settings(new: bool, context: CallbackContext) -> str:
    t, r = context.chat_data.get("temp-sources"), context.chat_data.get("rain-sources")
    current = f"{'Теперь' if new else 'В данный момент'} на графиках:\n\n-  температура из {', '.join(t)}\n"
    if len(r) > 0:
        current += f"-  осадки из {', '.join(r)}"
    else:
        current += "-  осадки не отображаются"
    return current


async def settings(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(current_settings(False, context))
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("температуру", callback_data=str(T_SETTINGS)),
                                    InlineKeyboardButton("осадки", callback_data=str(R_SETTINGS))
                                    ]])
    await update.message.reply_text("Вы можете изменить, с каких сайтов брать: ", reply_markup=markup)
    return CHOOSING_SETTING


async def temp_option(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    reply_markup = InlineKeyboardMarkup(source_keyboard())
    d = {k: False for k in sites}
    context.chat_data["temp-select"] = d
    await query.edit_message_text(text=source_choose_text('temp'),
                                  reply_markup=reply_markup)

    return T_SETTINGS


async def rain_option(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    reply_markup = InlineKeyboardMarkup(source_keyboard())
    d = {k: False for k in sites}
    context.chat_data["rain-select"] = d
    await query.edit_message_text(text=source_choose_text('rain'), reply_markup=reply_markup)
    return R_SETTINGS


def source_choose_text(mode: Union['temp', 'rain']):
    if mode == 'temp':
        return "Выберите сайты, температура с которых будет отображаться:\n"
    if mode == 'rain':
        return "Выберите сайты, с которых будет отображаться количество осадков (в мм):\n"


async def handle_temp_sources(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    sub_option = query.data
    d = context.chat_data["temp-select"]
    if sub_option == "stop":
        some = np.any([d[s] for s in d.keys()])
        if some:
            context.chat_data['temp-sources'] = [s for s in d.keys() if d[s]]
            ls = [s for s in d.keys() if d[s]]
            selected = ", ".join(ls)
            await query.edit_message_text(f"Сделано.", reply_markup=None)
            del context.chat_data["temp-select"]
            await query.message.reply_text(current_settings(True, context))
            return ConversationHandler.END
        else:
            await query.edit_message_text(source_choose_text('temp') + "Требуется хотя бы один",
                                          reply_markup=InlineKeyboardMarkup(source_keyboard()))
            return T_SETTINGS
    else:
        d[sub_option] = not d[sub_option]
        context.chat_data["temp-select"] = d
        selected = "\n".join([s for s in d.keys() if d[s]])
        await query.edit_message_text(source_choose_text('temp') + selected,
                                      reply_markup=InlineKeyboardMarkup(source_keyboard()))

        return T_SETTINGS


async def handle_rain_sources(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    sub_option = query.data
    d = context.chat_data["rain-select"]
    if sub_option == "stop":
        some = np.any([d[s] for s in d.keys()])
        del context.chat_data["rain-select"]
        if some:
            context.chat_data['rain-sources'] = [s for s in d.keys() if d[s]]
            ls = [s for s in d.keys() if d[s]]

            await query.edit_message_text(f"Сделано.", reply_markup=None)
            await query.message.reply_text(current_settings(True, context))

            return ConversationHandler.END
        else:
            context.chat_data["rain-sources"] = []
            await query.edit_message_text("Сделано.", reply_markup=None)
            await query.message.reply_text(current_settings(True, context))
            return R_SETTINGS
    else:
        d[sub_option] = not d[sub_option]
        context.chat_data["rain-select"] = d
        selected = "\n".join([s for s in d.keys() if d[s]])
        await query.edit_message_text(source_choose_text('rain') + selected,
                                      reply_markup=InlineKeyboardMarkup(source_keyboard()))
        return R_SETTINGS


async def days(thing: Union[Update, CallbackQuery], context: CallbackContext) -> int:
    dates: list[date] = [datetime.today().date() + timedelta(days=i) for i in range(10)]
    date_names = {dates[0].strftime('%Y%m%d'): f"сегодня, {dates[0].strftime('%d.%m')}",
                  dates[1].strftime('%Y%m%d'): f"завтра, {dates[1].strftime('%d.%m')}"}
    for i in range(2, 10):
        date_names[dates[i].strftime('%Y%m%d')] = dates[i].strftime('%a, %d.%m')

    keys = list(date_names.keys())
    row1 = [InlineKeyboardButton(date_names[key], callback_data=key) for key in keys[:5]]
    row2 = [InlineKeyboardButton(date_names[key], callback_data=key) for key in keys[5:]]
    keyboard = [row1, row2]
    await thing.message.reply_text("Выберите день: ", reply_markup=InlineKeyboardMarkup(keyboard), )
    return CHOOSING_DAY


async def handle_day(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    d = datetime.strptime(query.data, "%Y%m%d")
    day = Day(d)
    await query.edit_message_text(f"Выбрано {day.D_month}, {day.day_name}")
    await send(query, context, d)

    return CHOOSING_DAY


async def handle_again(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "again":
        await query.message.delete()
        return await days(query, context)

async def debug(update: Update, context: CallbackContext):
    await update.message.reply_text(pformat(context.chat_data))

def main() -> None:
    persistence = PicklePersistence(filepath='bot_persitence', update_interval=5)
    application = Application.builder().token(TOKEN).persistence(persistence).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*завтра)сегодня(?!.*завтра).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today())))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*сегодня)завтра(?!.*сегодня).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today() + timedelta(days=1))))

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            CHOOSING_SETTING: [
                CallbackQueryHandler(temp_option, pattern='^' + str(T_SETTINGS) + '$'),
                CallbackQueryHandler(rain_option, pattern='^' + str(R_SETTINGS) + '$')
            ],
            T_SETTINGS: [
                CallbackQueryHandler(handle_temp_sources)
            ],
            R_SETTINGS: [
                CallbackQueryHandler(handle_rain_sources)
            ]
        },
        fallbacks=[CommandHandler("settings", settings)]
    )

    application.add_handler(settings_handler)
    entry_for_days = [MessageHandler(filters.TEXT & ~filters.COMMAND, days),
                      CallbackQueryHandler(handle_again)]
    days_handler = ConversationHandler(
        entry_points=entry_for_days,
        states={
            CHOOSING_DAY: [CallbackQueryHandler(handle_day)],
        },
        fallbacks=entry_for_days
    )
    application.add_handler(days_handler)
    application.add_handler(CommandHandler("debug", debug))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
