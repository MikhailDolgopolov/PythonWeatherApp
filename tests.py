import threading
from datetime import datetime, timedelta
from pprint import pprint
import time

from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import verify_city, get_closest_place_matches, get_closest_city
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker
from helpers import random_delay


# places = [
#           *get_closest_place_matches("Тула"),
#           *get_closest_place_matches("Хопилово"),
#           *get_closest_place_matches("Рассвет"),
#           *get_closest_place_matches("Выхино"), ]


v = get_closest_place_matches("Рассвет, Тула")[0]
print(v)
print(get_closest_city(v))