import os
import re
import asyncio
import logging
from datetime import datetime, timedelta, date
# from pprint import pprint
from typing import List, Tuple
from warnings import filterwarnings

import urllib3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
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

CHOOSING_DAY, REPEAT, CHOOSING_CITY, CHOOSING_POINT = range(4)
STOP_WORD = "OK"
EMPTY = "[ пусто ]"


async def reset_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data.clear()
    context.chat_data["forecast"] = Forecast()
    await context.bot.send_message(
        update.effective_chat.id,
        "Готов к работе."
    )
    return await get_city(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "Привет!")
    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "Вы можете узнать погоду практически в любом городе - просто отправьте мне его название."
    )
    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "Отправьте любое сообщение со словами 'сегодня' или 'завтра', и я отправлю соответствующий прогноз.\n"
        "Чтобы быстро выбрать другой день, отправьте 'погода' или 'прогноз'."
    )
    await asyncio.sleep(1)
    await context.bot.send_message(chat_id, "Вот пример моего прогноза:")
    await asyncio.sleep(1)
    await context.bot.send_photo(chat_id=chat_id, photo="data/images/demo.png")
    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "В графиках используются данные Open-Meteo.com:\n"
        "- температура\n"
        "- количество осадков в час\n"
        "- облачность\n"
        "- световой день\n"
    )

    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "Вы всегда будете получать актуальный прогноз - данные загружаются только по вашему запросу."
    )
    await asyncio.sleep(2)
    await context.bot.send_message(
        chat_id,
        "Также, можно попробовать узнать погоду в любой точке - просто отправьте мне координаты"
        " - два числа через запятую. Их можно скопировать, например, в Яндекс.Картах."
    )
    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "Вы можете узнать точку, выбранную для прогноза в данный момент, отправив сообщение со словом 'город'."
    )
    await asyncio.sleep(1)
    await context.bot.send_message(
        chat_id,
        "При любых проблемах всегда можно воспользоваться командой /cancel, чтобы начать работу с ботом заново."
    )
    return await reset_data(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Caught unhandled error")
    if isinstance(update, Update) and update.effective_chat:
        await context.bot.send_message(
            update.effective_chat.id,
            "Упс, что‑то пошло не так — попробуйте еще раз или /cancel."
        )


async def send(
        thing: Update | Message, context: ContextTypes.DEFAULT_TYPE, forecast_date: datetime
) -> int:
    chat_id = thing.effective_chat.id
    if "forecast" not in context.chat_data:
        await reset_data(thing, context)
    loading = await context.bot.send_message(chat_id, "Это может занять некоторое время...")

    forecast: Forecast = context.chat_data["forecast"]
    pic = render_forecast_data(
        forecast.fetch_forecast(forecast_date),
        forecast_date,
        city=forecast.place_name,
        uid=chat_id,
    )

    await context.bot.send_photo(chat_id=chat_id, photo=pic["path"])
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
    loading = await context.bot.send_message(update.effective_chat.id, "Подождите…")
    text = update.message.text
    matches = get_closest_city_matches(text)

    if not matches:
        await loading.delete()
        await context.bot.send_message(
            update.effective_chat.id,
            f"Извините, я не знаю, как интерпретировать ваше сообщение."
        )
        return ConversationHandler.END

    # build (coord, label) pairs
    choices: List[Tuple[str, str]] = []
    for loc in matches:
        lat, lon = loc.latitude, loc.longitude
        coord = f"{lat},{lon}"
        addr = loc.raw.get("address", {})
        name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or loc.raw.get("name")
        region = addr.get("state") or addr.get("region") or addr.get("county")
        country = addr.get("country")
        if not name:
            continue  # skip if we really have no name at all
        parts = [name]
        if region:  parts.append(region)
        if country: parts.append(country)
        label = ", ".join(parts)
        choices.append((coord, label))

    if not choices:
        await loading.delete()
        await context.bot.send_message(
            update.effective_chat.id,
            "Ничего подходящего не нашлось, попробуйте немного изменить запрос."
        )
        return ConversationHandler.END

    # store mapping
    context.chat_data["cities_select"] = {c: l for c, l in choices}

    # build keyboard from choices
    keyboard = [
        [InlineKeyboardButton(label, callback_data=coord)]
        for coord, label in choices
    ]
    keyboard.append([InlineKeyboardButton('Отменить', callback_data='cancel')])

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
    if query.data == "cancel":
        await query.message.edit_text("Выбор города отменён.", reply_markup=None)
        await get_city(query, context)
        return ConversationHandler.END
    coord = query.data
    address = context.chat_data["cities_select"].get(coord)
    if not address:
        await query.edit_message_text(f"Извините, при выборе этого города произошла ошибка")
        return await days(update, context)
    await query.edit_message_text(f"Вы выбрали город: {address}")
    # update forecast
    context.chat_data["forecast"] = context.chat_data["forecast"].find_city(address)
    return await days(update, context)


async def get_city(update: Update|CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    city = context.chat_data['forecast'].place_name
    await update.message.reply_text(f"В данный момент выбран город {city}")


async def ask_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    loading = await update.message.reply_text("Точка получена. Подождите...")
    forecast: Forecast = context.chat_data.get("forecast")
    coords_list = list(map(float, re.split(r"\s*,\s*", text)))
    coords = coords_list[0], coords_list[1]
    if not coords:
        await loading.delete()
    potential_place, distance = forecast.new_point_info(coords)
    context.chat_data['potential_place'] = potential_place
    await loading.delete()

    keyboard = [
        InlineKeyboardButton(STOP_WORD, callback_data=text),
        InlineKeyboardButton("Отменить", callback_data="cancel")
    ]
    await update.message.reply_text(f"Там находится {potential_place.display_name}.")
    await update.message.reply_text(
        f"Расстояние от этой точки до выбранной сейчас — {distance:.1f} км. Утвердить точку?",
        reply_markup=InlineKeyboardMarkup([keyboard])
    )
    return REPEAT


async def set_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Точка не была установлена.")
        return ConversationHandler.END

    context.chat_data["forecast"].change_current_place(context.chat_data["potential_place"])
    place = context.chat_data["forecast"].place_name
    await query.edit_message_text(f"Точка установлена: {place}")
    return await days(update, context)


async def generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Извините, это сообщение устарело. Давайте начнём заново."
    )
    await reset_data(update, context)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Возможно, что-то пошло не так. Попробуем начать заново.")
    await reset_data(update, context)
    return ConversationHandler.END


def main() -> None:
    persistence = PicklePersistence(filepath="bot_persistence", update_interval=5)
    app = Application.builder().token(TOKEN).persistence(persistence).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(re.compile(r"\bгород\b", re.IGNORECASE)), get_city))
    app.add_handler(MessageHandler(filters.Regex(re.compile("r\bпрогноз\b|\bпогода\b", re.IGNORECASE)), days))

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

    coord_pattern = r"-?\d{1,2}\.\d+,\s*-?\d{1,2}\.\d+"

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^\D*$') & ~filters.COMMAND, find_city),
            MessageHandler(filters.Regex(coord_pattern), ask_point),
            CallbackQueryHandler(handle_again, pattern="^again$"),
        ],
        states={
            CHOOSING_DAY: [CallbackQueryHandler(handle_day, pattern=r"^\d{6,8}$")],
            REPEAT: [CallbackQueryHandler(set_point, pattern=f"^{coord_pattern}$|^cancel$")],
            CHOOSING_CITY: [CallbackQueryHandler(handle_city)],
            CHOOSING_POINT: [CallbackQueryHandler(set_point, pattern=f"({coord_pattern}|cancel)")]
        },
        fallbacks=[
            MessageHandler(filters.ALL, cancel),
        ],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(generic_callback))
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
