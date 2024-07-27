from Day import Day
from ForecastData import ForecastData
from ForecastRendering import get_and_render
from Forecast import Forecast
from FileManager import delete_old_files
import time

from mail.emails import send_red_email

delete_old_files()

forecast = Forecast()

a = ForecastData(forecast, Day(0))
b = ForecastData(forecast, Day(1))
