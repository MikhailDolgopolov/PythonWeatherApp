import datetime
import pandas as pd
from matplotlib import pyplot as plt
from numpy import dtype

from ForecastData import ForecastData
from ForecastRendering import render_forecast_data, compare_history
from Forecast import Forecast
from FileManager import clean_old_files
import time

# clean_old_files()
compare_history(2)
# forecast = Forecast()
# start = time.time()
# today = ForecastData(forecast, 1)
# tomorrow = ForecastData(forecast, 2)
# end = time.time()
# print(f"fetching took {end-start} seconds")
#
# render_forecast_data(today)
# render_forecast_data(tomorrow)

