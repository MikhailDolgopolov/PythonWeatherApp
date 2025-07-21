from datetime import datetime

from Forecast import Forecast
from ForecastRendering import render_forecast_data

f = Forecast()
d = datetime.today()
render_forecast_data(f.fetch_forecast(d), d, city=f.place_name, save=False)

