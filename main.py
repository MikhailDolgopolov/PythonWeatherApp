import datetime
import pandas as pd
from matplotlib import pyplot as plt
from numpy import dtype

from ForecastData import ForecastData
from ForecastRendering import ForecastRendering
from Forecast import Forecast
import time

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters

forecast = Forecast()
start = time.time()
data = ForecastData(forecast.fetch_forecast(2))
end = time.time()
print(f"fetching took {end-start} seconds")

ForecastRendering().show_data(data)

