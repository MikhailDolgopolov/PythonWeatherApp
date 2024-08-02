from datetime import datetime, timedelta

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from ForecastRendering import get_and_render
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser
from Parsers.OpenMeteoParser import OpenmeteoParser


f = GismeteoParser().get_weather(datetime.today() + timedelta(days=2))
print(f)



