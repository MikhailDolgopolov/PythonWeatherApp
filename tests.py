from datetime import datetime, timedelta

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from ForecastRendering import render_forecast_data
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser
from Parsers.OpenmeteoParser import OpenmeteoParser

forecast = Forecast(rainfall_sources=["Gismeteo"])

d = datetime.today()

render_forecast_data(forecast, d+timedelta(days=2), save=False, show=True)



