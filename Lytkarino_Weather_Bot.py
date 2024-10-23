
import logging
import os
import re
import time
from datetime import datetime, timedelta, date
from warnings import filterwarnings

import urllib3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import (
    Application,
    PicklePersistence,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackContext, filters, CallbackQueryHandler, TypeHandler)
from telegram.warnings import PTBUserWarning

from Day import Day
from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.CityNames import default_city
from Geography.Geography import get_closest_city_matches
from helpers import inflect

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Telegram bot API token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logger = logging.getLogger(__name__)

CHOOSING_SETTING, R_SETTINGS, T_SETTINGS, = 0, 1, 2
CHOOSING_DAY, REPEAT = 3, 4
CHOOSING_CITY = 5
STOP_WORD = "OK"
EMPTY = "[ пусто ]"


def reset_data(context:CallbackContext, persistent:dict=None):
    if persistent is None:
        persistent = {}
    context.chat_data.clear()
    context.chat_data["forecast"] = Forecast()
    context.chat_data["city"] = 'Лыткарино, Московская область'
    context.chat_data.update(persistent)


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет!')
    time.sleep(1)
    await update.message.reply_text(
        "Отправьте любое сообщение со словами 'сегодня' или 'завтра', и я отправлю соответствующий прогноз.\n"
        "Чтобы быстро выбрать другой день, отправьте 'погода' или 'прогноз'.")
    time.sleep(2)
    await update.message.reply_text(f"Чтобы посмотреть погоду не в {inflect(default_city, 'loct').title()}, просто отправьте мне название города. \n"
                                    "Любое другое сообщение тоже позволит выбрать день.")
    time.sleep(2.5)
    await update.message.reply_text(
        "Openmeteo позволяет посмотреть погоду в любой точке. Для этого отправьте координаты в формате 35.7, 37.6 и подтвердите выбор.")
    time.sleep(3)
    await update.message.reply_text("Вот пример моей работы:")
    time.sleep(1)
    await context.bot.send_photo(chat_id=update.message.chat_id, photo="data/images/demo.png")
    time.sleep(2)
    await update.message.reply_text("""На графике показаны:
    - температура из Open-Meteo.com
    - количество осадков в час
    - световой день
    """)

    reset_data(context)




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


async def find_city(update: Update, context: CallbackContext):
    if 'city' not in context.chat_data or 'forecast' not in context.chat_data:
        await context.bot.send_message(update.effective_chat.id, "Сначала введите /start")
        return ConversationHandler.END
    loading = await update.message.reply_text("Подождите...")
    cities = get_closest_city_matches(update.message.text)
    if cities and len(cities)>0:
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
        keyboard.append([InlineKeyboardButton(text="Отменить", callback_data="cancel")])
        await context.bot.delete_message(update.message.chat_id, loading.message_id)

        await context.bot.send_message(update.effective_chat.id, "Выберите город, который имеете в виду:",
                                        reply_markup=InlineKeyboardMarkup(keyboard))

        return CHOOSING_CITY
    else:
        await context.bot.delete_message(update.effective_chat.id, loading.message_id)
        await context.bot.send_message(update.effective_chat.id,
                                       text=f"Не получилось распознать '{update.message.text}' как город.")
        time.sleep(0.5)
        return await days(update, context, text=f"Выберите день для прогноза в {inflect(context.chat_data['city'].split(', ')[0], 'loct').title()}:")


async def handle_city(update: Update, context: CallbackContext) -> int:
    if 'city' not in context.chat_data or 'forecast' not in context.chat_data:
        await context.bot.send_message(update.effective_chat.id, "Сначала введите /start")
        return ConversationHandler.END
    query = update.callback_query
    await query.answer()
    loading = await context.bot.send_message(update.effective_chat.id, "Обрабатываю ваш выбор...")
    if query.data == "cancel":
        await context.bot.delete_message(update.effective_chat.id, loading.message_id)
        await query.edit_message_text("Город не был изменён.", reply_markup=None)
        return ConversationHandler.END
    full_city = context.chat_data['cities_select'][query.data]
    keyboard = [[InlineKeyboardButton(text=full_city, callback_data='None')]]
    await query.edit_message_text("Вы выбрали город", reply_markup=InlineKeyboardMarkup(keyboard))
    return await click_city(update, context, full_city, loading)

async def click_city(update:Update, context: CallbackContext, address: str, message:Message=None) -> int:
    if 'city' not in context.chat_data or 'forecast' not in context.chat_data:
        await context.bot.send_message(update.effective_chat.id, "Сначала введите /start")
        return ConversationHandler.END
    context.chat_data['city'] = address

    context.chat_data['forecast'] = context.chat_data['forecast'].find_city(address)
    if message: await context.bot.delete_message(update.effective_chat.id, message.message_id)
    return await days(update, context)


async def get_city(update: Update, context: CallbackContext):
    if 'city' not in context.chat_data: reset_data(context)
    city = context.chat_data['city']
    await update.message.reply_text(f"В данный момент выбран город {city}")


async def ask_point(update: Update, context: CallbackContext):
    persist = {"edit_point":await update.message.reply_text("Точка получена. Подождите...")}
    if 'forecast' not in context.chat_data or 'city' not in context.chat_data: reset_data(context, persist)


    forecast:Forecast = context.chat_data['forecast']
    coords = update.message.text
    point = forecast.point_info(coords)

    if isinstance(point, str):
        return ConversationHandler.END
    if isinstance(point, float):
        keyboard = [[InlineKeyboardButton(text=STOP_WORD, callback_data=coords), InlineKeyboardButton(text="Отменить", callback_data="cancel")]]
        await context.bot.send_message(update.effective_chat.id, f"Расстояние от этой точки до выбранной сейчас — {point} км. Утвердить точку?",
                                       reply_markup=InlineKeyboardMarkup(keyboard))


async def internal_error(update: Update, context: CallbackContext) -> int:
    await context.bot.send_message(update.effective_chat.id, "Извините, что-то пошло не так.")
    return ConversationHandler.END

async def set_point(update:Update, context:CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.message.delete()
        await context.bot.delete_message(update.effective_chat.id, message_id=context.chat_data['edit_point'].id)
        return ConversationHandler.END
    await context.bot.send_message(update.effective_chat.id, f"Подождите...")
    context.chat_data["forecast"].set_openmeteo_point(query.data)
    await context.bot.send_message(update.effective_chat.id, f"Точка установлена: {context.chat_data['forecast'].place.full_str()}")
    return await days(update, context)


def main() -> None:
    persistence = PicklePersistence(filepath='data/bot_persitence', update_interval=5)
    application = Application.builder().token(TOKEN).persistence(persistence).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex(re.compile('город', re.IGNORECASE)), get_city))
    application.add_handler(MessageHandler(filters.Regex(re.compile('прогноз|погода', re.IGNORECASE)), days))

    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*завтра)сегодня(?!.*завтра).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today())))
    application.add_handler(
        MessageHandler(filters.Regex(re.compile(r'^(?!.*сегодня)завтра(?!.*сегодня).*$', re.IGNORECASE)),
                       lambda update, context: send(update, context, datetime.today() + timedelta(days=1))))

    coords_regex = r"-?\d{1,2}\.\d+,\s+-?\d{1,2}\.\d+"
    application.add_handler(MessageHandler(filters.Regex(coords_regex), ask_point))

    application.add_handler(CallbackQueryHandler(set_point, pattern="|".join([coords_regex, "cancel"])))
    entry_for_days = [MessageHandler(filters.TEXT & ~filters.COMMAND, find_city),
                      CallbackQueryHandler(handle_again, pattern=r'again')]
    days_handler = ConversationHandler(
        entry_points=entry_for_days,
        states={
            CHOOSING_DAY: [CallbackQueryHandler(handle_day, pattern=r'\d{6,8}')],
            REPEAT: [CallbackQueryHandler(handle_again)],
            CHOOSING_CITY: [CallbackQueryHandler(handle_city)]
        },
        fallbacks=[TypeHandler(Update, internal_error)]
    )

    application.add_handler(days_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
