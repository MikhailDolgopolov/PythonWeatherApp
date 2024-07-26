from Day import Day
from ForecastData import ForecastData
from ForecastRendering import render_forecast_data
from Forecast import Forecast
from FileManager import delete_old_files
import time

from mail.emails import send_my_email, send_red_email

delete_old_files()
forecast = Forecast()
start = time.time()
today = Day(0)
tomorrow = Day(1)
today_forecast = ForecastData(forecast, today)
tomorrow_forecast = ForecastData(forecast, tomorrow)
end = time.time()
print(f"fetching took {end-start} seconds")


fig1 = render_forecast_data(today_forecast)
fig2 = render_forecast_data(tomorrow_forecast)

send_red_email(fig1, fig2)
