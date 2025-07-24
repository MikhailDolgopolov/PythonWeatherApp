from datetime import datetime, timedelta
from pprint import pprint

from Forecast import Forecast
from ForecastRendering import render_forecast_data
from Geography.Geography import get_closest_city_matches

f = Forecast('Сочи')
d = datetime.today()+timedelta(days=1)
render_forecast_data(f.fetch_forecast(d), d, city=f.place_name, save=False)

