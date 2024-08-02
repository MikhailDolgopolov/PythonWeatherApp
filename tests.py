from datetime import datetime, timedelta

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from ForecastRendering import get_and_render
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser
from Parsers.OpenMeteoParser import OpenmeteoParser


p = OpenmeteoParser().get_weather(datetime.today()+timedelta(days=3))


def get_last_forecast_update(self, date: datetime) -> datetime:
    raise NotImplementedError("Subclasses should implement this method")

