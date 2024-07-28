from Day import Day
from ForecastData import ForecastData
from Forecast import Forecast
from FileManager import delete_old_files

delete_old_files()

forecast = Forecast()

a = ForecastData(forecast, Day(0))
b = ForecastData(forecast, Day(1))
