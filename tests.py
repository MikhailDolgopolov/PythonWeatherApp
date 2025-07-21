import threading
from datetime import datetime, timedelta
from pprint import pprint
import time

from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import verify_city, get_closest_city_matches
from helpers import random_delay


f = Forecast()
d = datetime.today()
render_forecast_data(f.fetch_forecast(d), d, city=f.place_name, save=False)

