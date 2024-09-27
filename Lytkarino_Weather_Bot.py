import asyncio
import os
from datetime import datetime, timedelta, date
import logging
import re
import threading
import time
from pprint import pformat, pprint
from typing import Literal

import numpy as np
import urllib3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
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
from Geography.Geography import get_closest_city_matches
from geopy.distance import geodesic
from helpers import read_json, random_delay

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("WDM").setLevel(logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Telegram bot API token
TOKEN = read_json("secrets.json")["telegram_token"]

logger = logging.getLogger(__name__)

CHOOSING_SETTING, R_SETTINGS, T_SETTINGS, = 0, 1, 2
CHOOSING_DAY, REPEAT = 3, 4
CHOOSING_CITY = 5
STOP_WORD = "OK"
EMPTY = "[ пусто ]"

sites = Forecast.all_sources()
default_sources = [
    # "Foreca",
    "Openmeteo"]


def source_keyboard():
    keyboard = [[InlineKeyboardButton(s, callback_data=s)] for s in sites]
    keyboard.append([InlineKeyboardButton(STOP_WORD, callback_data="stop")])
    return keyboard

def reset_data(context:CallbackContext):
    context.chat_data.clear()
    context.chat_data["temp-sources"] = default_sources
    context.chat_data["rain-sources"] = default_sources
    context.chat_data["forecast"] = Forecast(temp_sources=default_sources, rain_sources=default_sources)
    context.chat_data["city"] = 'Лыткарино, Московская область'


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет!')
    time.sleep(1)
    await update.message.reply_text(
        "Отправьте любое сообщение со словами 'сегодня' или 'завтра', и я отправлю соответствующий прогноз.\n"
        "Чтобы быстро выбрать другой день, отправьте 'погода' или 'прогноз'.")
    time.sleep(3)
    await update.message.reply_text("Чтобы посмотреть погоду не в Лыткарино, просто отправьте мне название города. \n"
                                    "Любое другое сообщение тоже позволит выбрать день.")
    time.sleep(3)
    await update.message.reply_text("Вот пример моей работы:")
    time.sleep(1)
    await context.bot.send_photo(chat_id=update.message.chat_id, photo="demo.png")
    time.sleep(2)
    await update.message.reply_text("""На графике показаны:
    - температура из трёх источников (Foreca.ru, Gismeteo.ru, Open-Meteo.com)
    - количество осадков в час
    - световой день
    """)
    time.sleep(2)
    await update.message.reply_text(
        "Также можно настроить, из данных каких сайтов будут показаны температура и осадки. Для этого используйте команду /settings")

    reset_data(context)

    await update.message.reply_text(current_settings(False, context))


def periodic_task():
    print("Auto-updates started")
    forecast = Forecast()
    while True:
        forecast.clear_files()
        for i in range(5):
            forecast.load_new_data(datetime.today() + timedelta(days=i))
            # random_delay()
        print('\n\n')
        time.sleep(3600 * 2.5)


async def send(thing: Update, context: CallbackContext, forecast_date: datetime) -> int:
    chat_id = thing.effective_chat.id
    initial_message = await context.bot.send_message(chat_id, text='Это может занять некоторое время...')
    if 'city' not in context.chat_data or 'forecast' not in context.chat_data:
        reset_data(context)

    forecast = context.chat_data['forecast']
    pic = render_forecast_data(forecast.fetch_forecast(forecast_date), forecast_date,
                               city=context.chat_data.get('city', None), uid=chat_id)

    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"], caption=forecast.last_updated(forecast_date).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"))
    await initial_message.delete()
    os.remove(pic["path"])

    keyboard = [[InlineKeyboardButton("Выбрать день", callback_data="again")]]
    time.sleep(1)
    await context.bot.send_message(chat_id, text="прогноз на 9 дней вперед", reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSING_DAY


def current_settings(new: bool, context: CallbackContext) -> str:
    if 'city' not in context.chat_data or 'forecast' not in context.chat_data:
        reset_data(context)
    t, r = context.chat_data.get("temp-sources"), context.chat_data.get("rain-sources")
    current = f"{'Теперь' if new else 'В данный момент'} на графиках погоды:\n\n-  температура из {', '.join(t)}\n"
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
    await query.edit_message_text(text=source_choose_text('temp') + EMPTY,
                                  reply_markup=reply_markup)

    return T_SETTINGS


async def rain_option(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    reply_markup = InlineKeyboardMarkup(source_keyboard())
    await query.edit_message_text(text=source_choose_text('rain') + EMPTY, reply_markup=reply_markup)
    return R_SETTINGS


def source_choose_text(mode: Literal['temp', 'rain']):
    if mode == 'temp':
        return "Выберите сайты, температура с которых будет отображаться:\n"
    if mode == 'rain':
        return "Выберите сайты, с которых будет отображаться количество осадков (в мм):\n"


async def handle_temp_sources(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    sub_option = query.data
    d = context.chat_data.get("temp-select", {s: False for s in sites})
    if sub_option == "stop":
        some = np.any([d[s] for s in d.keys()])
        if some:
            loading = await context.bot.send_message(update.effective_chat.id, "Подождите...")
            if "temp-select" in context.chat_data:
                del context.chat_data["temp-select"]
            result = [s for s in d.keys() if d[s]]
            context.chat_data['temp-sources'] = result
            context.chat_data['forecast'].change_temp_sources(result)

            await loading.delete()
            await context.bot.send_message(update.effective_chat.id, f"Источники температуры изменены.")
            key = [[InlineKeyboardButton("Изменить осадки", callback_data="rain")]]
            await context.bot.send_message(update.effective_chat.id, text=current_settings(True, context))
            time.sleep(1)
            await context.bot.send_message(update.effective_chat.id,
                                           text="Также можно", reply_markup=InlineKeyboardMarkup(key))
            return T_SETTINGS
        else:
            await query.edit_message_text(source_choose_text('temp') + "Требуется хотя бы один",
                                          reply_markup=InlineKeyboardMarkup(source_keyboard()))

            return T_SETTINGS
    else:
        d[sub_option] = not d[sub_option]
        context.chat_data["temp-select"] = d
        selected = ''.join(["\n- " + s for s in d.keys() if d[s]])
        if selected == "": selected = EMPTY
        await query.edit_message_text(source_choose_text('temp') + selected,
                                      reply_markup=InlineKeyboardMarkup(source_keyboard()))

        return T_SETTINGS


async def handle_rain_sources(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    sub_option = query.data
    d = context.chat_data.get("rain-select", {s: False for s in sites})
    if sub_option == "stop":
        loading = await context.bot.send_message(update.effective_chat.id, "Подождите...")
        if "rain-select" in context.chat_data:
            del context.chat_data["rain-select"]
        result = [s for s in d.keys() if d[s]]
        context.chat_data['rain-sources'] = result
        context.chat_data['forecast'].change_rain_sources(result)
        await loading.delete()
        await context.bot.send_message(update.effective_chat.id,f"Источники осадков изменены.")
        key = [[InlineKeyboardButton("Изменить источники температуры", callback_data="temp")]]
        await context.bot.send_message(update.effective_chat.id, text=current_settings(True, context))
        time.sleep(1)
        await context.bot.send_message(update.effective_chat.id,
                                       text="Также можно", reply_markup=InlineKeyboardMarkup(key))
        return R_SETTINGS
    else:
        d[sub_option] = not d[sub_option]
        context.chat_data["rain-select"] = d
        selected = "".join(["\n-  " + s for s in d.keys() if d[s]])
        if selected == "": selected = "Без осадков"
        await query.edit_message_text(source_choose_text('rain') + selected,
                                      reply_markup=InlineKeyboardMarkup(source_keyboard()))
        return R_SETTINGS


async def days(update: Update, context: CallbackContext, text:str=None) -> int:
    dates: list[date] = [datetime.today().date() + timedelta(days=i) for i in range(10)]
    date_names = {dates[0].strftime('%Y%m%d'): f"сегодня, {dates[0].strftime('%d.%m')}",
                  dates[1].strftime('%Y%m%d'): f"завтра, {dates[1].strftime('%d.%m')}"}
    for i in range(2, 10):
        date_names[dates[i].strftime('%Y%m%d')] = dates[i].strftime('%a, %d.%m')

    keys = list(date_names.keys())
    row1 = [InlineKeyboardButton(date_names[key], callback_data=key) for key in keys[:5]]
    row2 = [InlineKeyboardButton(date_names[key], callback_data=key) for key in keys[5:]]
    keyboard = [row1, row2]
    if not text: text = "Выберите день: "
    await context.bot.send_message(update.effective_chat.id, text, reply_markup=InlineKeyboardMarkup(keyboard), )
    return CHOOSING_DAY


async def handle_day(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    d = datetime.strptime(query.data, "%Y%m%d")
    day = Day(d)
    await query.edit_message_text(f"Выбрано {day.D_month}, {day.day_name}")
    await send(update, context, d)

    return CHOOSING_DAY


async def handle_again(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "again":
        await query.message.delete()
        return await days(update, context)


async def handle_one_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "temp":
        await temp_option(update, context)
        return T_SETTINGS
    if query.data == "rain":
        await rain_option(update, context)
        return R_SETTINGS


async def debug(update: Update, context: CallbackContext):
    await update.message.reply_text(pformat(context.chat_data))


async def find_city(update: Update, context: CallbackContext):
    cities = get_closest_city_matches(update.message.text)
    loading = await update.message.reply_text("Подождите...")

    if cities:
        coors = [str((loc.latitude, loc.longitude)) for loc in cities]
        data = [city.raw['address'] for city in cities]

        names = [address.get('city') or address.get('town') or address.get('village')
                 or address.get('neighbourhood') or address.get('suburb') for address in data]
        states = [
            address.get('state') or address.get('region') or address.get('county') or address.get('state_district')
            for address in data]
        try:
            states = [data[i].get('region') or data[i].get('state_district') or data[i].get('county')
                      if names[i] in states[i] else states[i] for i in range(len(cities))]
        except: pass
        states = [f"{states[i]}, {data[i]['country']}" if len(states[i])<20 else states[i] for i in range(len(cities))]
        addresses = [f"{names[i]}, {states[i]}" if states[i] else names[i] for i in range(len(cities))]

        context.chat_data['cities_select'] = {coors[i]: addresses[i] for i in range(len(cities))}

        keyboard = [[InlineKeyboardButton(text=addresses[i], callback_data=coors[i])] for i in range(len(cities))]

        await context.bot.delete_message(update.message.chat_id, loading.message_id)

        await context.bot.send_message(update.effective_chat.id, "Выберите город, который имеете в виду:",
                                        reply_markup=InlineKeyboardMarkup(keyboard))

        return CHOOSING_CITY
    else:
        await context.bot.delete_message(update.effective_chat.id, loading.message_id)
        await context.bot.send_message(update.effective_chat.id,
                                       text=f"Не получилось распознать '{update.message.text}' как город.")
        time.sleep(0.5)
        return await days(update, context, text=f"Выберите день для прогноза в {context.chat_data['city'].split(', ')[0]}:")


async def handle_city(update: Update, context: CallbackContext) -> int:
    if 'city' not in context.chat_data or 'forecast' not in context.chat_data:
        reset_data(context)
    query = update.callback_query
    await query.answer()
    loading = await context.bot.send_message(update.effective_chat.id, "Обрабатываю ваш выбор...")
    full_city = context.chat_data['cities_select'][query.data]
    keyboard = [[InlineKeyboardButton(text=full_city, callback_data='None')]]
    await query.edit_message_text("Вы выбрали город", reply_markup=InlineKeyboardMarkup(keyboard))
    return await click_city(update, context, full_city, loading)

async def click_city(update:Update, context: CallbackContext, address: str, message:Message=None) -> int:
    if 'city' not in context.chat_data or 'forecast' not in context.chat_data:
        reset_data(context)
    context.chat_data['city'] = address

    context.chat_data['forecast'] = context.chat_data['forecast'].find_city(address)
    if message: await context.bot.delete_message(update.effective_chat.id, message.message_id)
    return await days(update, context)


async def get_city(update: Update, context: CallbackContext):
    if 'city' not in context.chat_data: reset_data(context)
    city = context.chat_data['city']
    await update.message.reply_text(f"В данный момент выбран город {city}")

async def ask_point(update: Update, context: CallbackContext):
    await update.message.reply_text("Точка получена. Подождите...")

    if 'forecast' not in context.chat_data: reset_data(context)
    forecast:Forecast = context.chat_data['forecast']
    coords = update.message.text
    arr = coords.split(",")
    point = forecast.point_info(coords)
    # await update.message.reply_text(f"got info {point}")
    if isinstance(point, str): await context.bot.send_message(update.effective_chat.id, f"{point}")
    if isinstance(point, float):
        keyboard = [[InlineKeyboardButton(text=STOP_WORD, callback_data=coords), InlineKeyboardButton(text="Отменить", callback_data="cancel")]]
        await context.bot.send_message(update.effective_chat.id, f"Расстояние от точки до выбранного сейчас города {point} км. Утвердить точку?",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # await context.bot.send_message(update.effective_chat.id, f"Looking for {coords}")


async def set_point(update:Update, context:CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        return
    await context.bot.send_message(update.effective_chat.id, f"Подождите...")
    context.chat_data["forecast"].set_openmeteo_point(query.data)
    await context.bot.send_message(update.effective_chat.id, f"Точка установлена")


def main() -> None:
    persistence = PicklePersistence(filepath='bot_persitence', update_interval=5)
    application = Application.builder().token(TOKEN).persistence(persistence).build()
    threading.Thread(target=periodic_task, daemon=True).start()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex(re.compile('город', re.IGNORECASE)), get_city))
    application.add_handler(MessageHandler(filters.Regex(re.compile('прогноз|погода', re.IGNORECASE)), days))
    coords_regex = r"-?\d{1,2}\.\d+,\s+-?\d{1,2}\.\d+"
    application.add_handler(MessageHandler(filters.Regex(coords_regex), ask_point))
    application.add_handler(CallbackQueryHandler(set_point, pattern="|".join([coords_regex, "cancel"])))

    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*завтра)сегодня(?!.*завтра).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today())))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*сегодня)завтра(?!.*сегодня).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today() + timedelta(days=1))))

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings),
                      CallbackQueryHandler(handle_one_button, pattern='temp|rain')],
        states={
            CHOOSING_SETTING: [
                CallbackQueryHandler(temp_option, pattern='^' + str(T_SETTINGS) + '$'),
                CallbackQueryHandler(rain_option, pattern='^' + str(R_SETTINGS) + '$')
            ],
            T_SETTINGS: [
                CallbackQueryHandler(handle_temp_sources, pattern='|'.join([*sites, "stop"])),
                CallbackQueryHandler(handle_one_button, pattern='rain')
            ],
            R_SETTINGS: [
                CallbackQueryHandler(handle_rain_sources, pattern='|'.join([*sites, "stop"])),
                CallbackQueryHandler(handle_one_button, pattern='temp')
            ]
        },
        fallbacks=[CommandHandler("settings", settings)]
    )

    application.add_handler(settings_handler)
    entry_for_days = [MessageHandler(filters.TEXT & ~filters.COMMAND, find_city),
                      CallbackQueryHandler(handle_again, pattern=r'again')]
    days_handler = ConversationHandler(
        entry_points=entry_for_days,
        states={
            CHOOSING_DAY: [CallbackQueryHandler(handle_day, pattern=r'\d{6,8}')],
            REPEAT: [CallbackQueryHandler(handle_again)],
            CHOOSING_CITY: [CallbackQueryHandler(handle_city)]
        },
        fallbacks=entry_for_days
    )

    application.add_handler(days_handler)

    # application.add_handler(CommandHandler("debug", debug))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
