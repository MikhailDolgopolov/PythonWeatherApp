import threading
from datetime import datetime, timedelta
from pprint import pprint
import time

from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import verify_city, get_closest_city_matches
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker
from helpers import random_delay


# input_string = "Воркута"

# cities = get_closest_city_matches(input_string)
forecast = Forecast(mode="Seeker")
for i in range(10, 14):
    d = datetime(2024, 8, i)
    c=0
    while c<3:
        try:
            data = forecast.fetch_forecast(d)
            render_forecast_data(data, d, "Лыткарино, Московская область", save=True)
            break
        except:
            random_delay(1,5)
        finally:
            c+=1

# if not cities:
     # print("Not found ", input_string)
# else:
#     data = [city.raw['address'] for city in cities]
#     pprint(data[0])
#     # print('city' in data[0])
#     names = [address.get('city') or address.get('town') or address.get('village') for address in data]
#     states = [address.get('state') or address.get('region') or address.get('county') or address.get('state_district')
#               for address in data]
#     states = [data[i].get('region') or data[i].get('state_district') or data[i].get('county')
#               if names[i] in states[i] else states[i] for i in range(len(cities))]
#     addresses = [f"{names[i]}, {states[i]}" if states[i] else names[i] for i in range(len(cities))]
#     print(addresses)
#
#     city = addresses[0]
#     d = datetime.today()+timedelta(days=1)
#     foreca = ForecaSeeker(headless=False).find_city(city).get_weather(d)
#     # data = forecast.load_new_data(date=d)
#     print(foreca)
#     # render_forecast_data(data, d, city.split(", ")[0], save=False, show=True)