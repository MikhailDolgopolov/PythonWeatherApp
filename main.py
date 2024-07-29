from Day import Day
from ForecastData import ForecastData
from Forecast import Forecast
from FileManager import delete_old_files
from ForecastRendering import get_and_render
from email_sender import send_red_email

delete_old_files()

forecast = Forecast()

a = ForecastData(forecast, Day(0))
b = ForecastData(forecast, Day(1))

send_red_email(get_and_render(0), get_and_render(1))
