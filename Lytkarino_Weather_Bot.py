import os
import re
import asyncio
import logging
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
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.warnings import PTBUserWarning

from Day import Day
from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import get_closest_city_matches
from helpers import read_json

# Suppress PTB warning about CallbackQueryHandler filters
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.ERROR)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = read_json("secrets.json")["telegram_token"]
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_SETTING, R_SETTINGS, T_SETTINGS = range(3)
CHOOSING_DAY, REPEAT, CHOOSING_CITY = range(3, 6)
STOP_WORD = "OK"
EMPTY = "[ пусто ]"


def reset_data(context: ContextTypes.DEFAULT_TYPE):
    context.chat_data.clear()
    context.chat_data["forecast"] = Forecast()
    context.chat_data["city"] = "Лыткарино, Московская область"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "Привет!")
    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "Отправьте любое сообщение со словами 'сегодня' или 'завтра', и я отправлю соответствующий прогноз.\n"
        "Чтобы быстро выбрать другой день, отправьте 'погода' или 'прогноз'."
    )
    await asyncio.sleep(3)
    await context.bot.send_message(
        chat_id,
        "Чтобы посмотреть погоду не в Лыткарино, просто отправьте мне название города. \n"
        "Любое другое сообщение тоже позволит выбрать день."
    )
    await asyncio.sleep(3)
    await context.bot.send_message(chat_id, "Вот пример моей работы:")
    await asyncio.sleep(1)
    await context.bot.send_photo(chat_id=chat_id, photo="demo.png")
    await asyncio.sleep(2)
    await context.bot.send_message(
        chat_id,
        "На графике показаны:\n"
        "- температура из Open-Meteo.com\n"
        "- количество осадков в час\n"
        "- световой день"
    )
    reset_data(context)


async def send(
        thing: Update | Message, context: ContextTypes.DEFAULT_TYPE, forecast_date: datetime
) -> int:
    chat_id = thing.effective_chat.id
    loading = await context.bot.send_message(chat_id, "Это может занять некоторое время...")
    if "city" not in context.chat_data or "forecast" not in context.chat_data:
        reset_data(context)

    forecast: Forecast = context.chat_data["forecast"]
    pic = render_forecast_data(
        forecast.fetch_forecast(forecast_date),
        forecast_date,
        city=context.chat_data.get("city", None),
        uid=chat_id,
    )

    caption = forecast.last_updated(forecast_date).strftime(
        "Данные в последний раз обновлены %d.%m.%Y, в %H:%M"
    )
    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"], caption=caption)
    await loading.delete()
    os.remove(pic["path"])

    keyboard = [[InlineKeyboardButton("Выбрать день", callback_data="again")]]
    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "прогноз на 9 дней вперед",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_DAY


async def days(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = None) -> int:
    today = date.today()
    dates = [today + timedelta(days=i) for i in range(10)]
    date_names = {
        dates[0].strftime("%Y%m%d"): f"сегодня, {dates[0]:%d.%m}",
        dates[1].strftime("%Y%m%d"): f"завтра, {dates[1]:%d.%m}",
    }
    for i in range(2, 10):
        date_names[dates[i].strftime("%Y%m%d")] = dates[i].strftime("%a, %d.%m")

    keys = list(date_names)
    row1 = [InlineKeyboardButton(date_names[k], callback_data=k) for k in keys[:5]]
    row2 = [InlineKeyboardButton(date_names[k], callback_data=k) for k in keys[5:]]
    keyboard = [row1, row2]

    prompt = text or "Выберите день:"
    await context.bot.send_message(
        update.effective_chat.id,
        prompt,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_DAY


async def handle_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    d = datetime.strptime(query.data, "%Y%m%d")
    day = Day(d)
    await query.edit_message_text(f"Выбрано {day.D_month}, {day.day_name}")
    return await send(update, context, d)


async def handle_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "again":
        await query.message.delete()
    return await days(update, context)


async def find_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    matches = get_closest_city_matches(text)
    loading = await update.message.reply_text("Подождите...")
    if not matches:
        await loading.delete()
        await context.bot.send_message(
            update.effective_chat.id,
            f"Не получилось распознать '{text}' как город."
        )
        return await days(
            update, context,
            text=f"Выберите день для прогноза в {context.chat_data.get('city', '')}:"
        )

    coords = [f"{loc.latitude},{loc.longitude}" for loc in matches]
    addresses = []
    for loc in matches:
        addr = loc.raw["address"]
        name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb")
        region = addr.get("state") or addr.get("region") or addr.get("county")
        country = addr.get("country")
        addresses.append(f"{name}, {region}, {country}")

    context.chat_data["cities_select"] = dict(zip(coords, addresses))
    keyboard = [[InlineKeyboardButton(addresses[i], callback_data=coords[i])]
                for i in range(len(coords))]

    await loading.delete()
    await context.bot.send_message(
        update.effective_chat.id,
        "Выберите город, который имеете в виду:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_CITY


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    coord = query.data
    address = context.chat_data["cities_select"].get(coord)
    if not address:
        return await days(update, context)
    await query.edit_message_text(f"Вы выбрали город: {address}")
    # update forecast and city
    context.chat_data["city"] = address
    context.chat_data["forecast"] = context.chat_data["forecast"].find_city(address)
    return await days(update, context)


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    city = context.chat_data.get("city", "Лыткарино, Московская область")
    await update.message.reply_text(f"В данный момент выбран город {city}")


async def ask_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    loading = await update.message.reply_text("Точка получена. Подождите...")
    forecast: Forecast = context.chat_data.get("forecast", Forecast())
    result = forecast.point_info(text)
    await loading.delete()

    if isinstance(result, str):
        await update.message.reply_text(result)
        return ConversationHandler.END
    if isinstance(result, float):
        keyboard = [
            InlineKeyboardButton(STOP_WORD, callback_data=text),
            InlineKeyboardButton("Отменить", callback_data="cancel")
        ]
        await update.message.reply_text(
            f"Расстояние от этой точки до выбранной сейчас — {result:.1f} км. Утвердить точку?",
            reply_markup=InlineKeyboardMarkup([keyboard])
        )
        return REPEAT


async def set_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Точка не была установлена.")
        return ConversationHandler.END

    coords = query.data
    context.chat_data["forecast"].set_openmeteo_point(coords)
    place = context.chat_data["forecast"].place.full_str()
    await query.edit_message_text(f"Точка установлена: {place}")
    return await days(update, context)


def main() -> None:
    persistence = PicklePersistence(filepath="bot_persistence", update_interval=5)
    app = Application.builder().token(TOKEN).persistence(persistence).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(re.compile("город", re.IGNORECASE)), get_city))
    app.add_handler(MessageHandler(filters.Regex(re.compile("прогноз|погода", re.IGNORECASE)), days))

    app.add_handler(
        MessageHandler(
            filters.Regex(re.compile(r"^(?!.*завтра)сегодня", re.IGNORECASE)),
            lambda u, c: send(u, c, datetime.now())
        )
    )
    app.add_handler(
        MessageHandler(
            filters.Regex(re.compile(r"^(?!.*сегодня)завтра", re.IGNORECASE)),
            lambda u, c: send(u, c, datetime.now() + timedelta(days=1))
        )
    )

    coord_pattern = r"^-?\d{1,2}\.\d+,-?\d{1,2}\.\d+$"
    app.add_handler(MessageHandler(filters.Regex(coord_pattern), ask_point))
    app.add_handler(CallbackQueryHandler(set_point, pattern=f"({coord_pattern}|cancel)"))

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_city),
            CallbackQueryHandler(handle_again, pattern="^again$")
        ],
        states={
            CHOOSING_DAY: [CallbackQueryHandler(handle_day, pattern=r"^\d{6,8}$")],
            REPEAT: [CallbackQueryHandler(set_point, pattern=f"^{coord_pattern}$|^cancel$")],
            CHOOSING_CITY: [CallbackQueryHandler(handle_city)],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_city),
            CallbackQueryHandler(handle_again, pattern="^again$")
        ],
    )
    app.add_handler(conv)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
