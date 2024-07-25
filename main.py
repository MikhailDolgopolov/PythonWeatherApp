import datetime
import pandas as pd
from matplotlib import pyplot as plt
from numpy import dtype

from ForecastData import ForecastData
from ForecastRendering import ForecastRendering
from Forecast import Forecast
import time

forecast = Forecast()
start = time.time()
today = ForecastData(forecast, 1)
tomorrow = ForecastData(forecast, 2)
end = time.time()
print(f"fetching took {end-start} seconds")

renderer = ForecastRendering()
renderer.render_data(today)
renderer.render_data(tomorrow)

