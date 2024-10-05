import threading
from datetime import datetime, timedelta
from pprint import pprint
import time

from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import verify_city, get_closest_city_matches, get_coordinates, what_is_there
from geopy.distance import geodesic
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker
from helpers import random_delay


# p = GismeteoParser(headless=False)
#
# p.get_weather(datetime.today())

loc = 'Москва'

s = "55.6,  38"
p = tuple(float(num) for num in s.split(", "))
# get_closest_city_matches(loc)

what_is_there(s)