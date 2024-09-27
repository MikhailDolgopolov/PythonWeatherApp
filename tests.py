import threading
from datetime import datetime, timedelta
from pprint import pprint
import time

from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import verify_city, get_closest_city_matches, get_coordinates
from geopy.distance import geodesic
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker
from helpers import random_delay


# p = GismeteoParser(headless=False)
#
# p.get_weather(datetime.today())

loc = 'Лыткарино, Московская область'
city_coords = get_coordinates(loc)

print(city_coords)

s = "55.6,  38"
p = tuple(float(num) for num in s.split(", "))
d = geodesic(city_coords, (p)).kilometers
print(d)