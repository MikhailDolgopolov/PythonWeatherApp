from datetime import datetime, timedelta
from pprint import pprint

from Day import Day
from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser
from Parsers.OpenmeteoParser import OpenmeteoParser
from Parsers.AccuweatherParser import AccuweatherParser

# forecast = Forecast(rainfall_sources=["Gismeteo"])
#
# d = datetime.today()
#
# render_forecast_data(forecast, d+timedelta(days=2), save=False, show=True)


p = AccuweatherParser()

print(p.find_location_key())

data = p.load_weather()

# pprint(data)
