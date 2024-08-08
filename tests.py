from datetime import datetime, timedelta
from pprint import pprint

from telegram import InlineKeyboardButton

from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import verify_city, get_closest_city_matches
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker

input_string = "Москва"
cities = get_closest_city_matches(input_string)
# forecast = Forecast(mode="Seeker")
if not cities:
    print("Not found ", input_string)
else:
    # data = [city.raw['address'] for city in cities]
    # # print(data[0]['city'])
    # # print('city' in data[0])
    # names = [address.get('city') or address.get('town') or address.get('village') for address in data]
    # states = [address.get('county') or address.get('state_district') or address.get('state') or address.get('region')
    #           for address in data]
    # states = [data[i].get('region') or data[i].get('state_district') or data[i].get('county')
    #           if names[i] == states[i] else states[i] for i in range(len(cities))]
    # addresses = [f"{names[i]}, {states[i]}" if states[i] else names[i] for i in range(len(cities))]

    # city = addresses[0]
    d = datetime.today()+timedelta(days=9)
    data = ForecaSeeker(headless=False).get_weather(date=d)
    print(data)
    # render_forecast_data(data, d, city.split(", ")[0], save=False, show=True)

