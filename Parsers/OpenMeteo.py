import numpy as np
import openmeteo_requests

import requests_cache
import pandas as pd
from matplotlib import pyplot as plt
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"


def get_open_meteo(day = 1):
	params = {
		"latitude": 55.57,
		"longitude": 35.91,
		"hourly": ["temperature_2m", "precipitation_probability", "precipitation", "rain", "wind_speed_10m"],
		"wind_speed_unit": "ms",
		"timezone": "Europe/Moscow",
		"forecast_days": day
	}
	responses = openmeteo.weather_api(url, params=params)

	# Process first location. Add a for-loop for multiple locations or weather models
	response = responses[0]

	# Process hourly data. The order of variables needs to be the same as requested.
	hourly = response.Hourly()
	hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
	hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
	hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
	hourly_rain = hourly.Variables(3).ValuesAsNumpy()
	hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()

	hourly_data = pd.date_range(
		start = pd.to_datetime(hourly.Time(), unit = "s"), #utc=True
		end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
		freq = pd.Timedelta(seconds = hourly.Interval()),
		inclusive = "left")


	h = np.arange(0, 24)
	if day==2:
		h=np.arange(-24, 24)
	arr = np.array([h, hourly_temperature_2m, hourly_precipitation, hourly_wind_speed_10m]).T
	if day==2:
		start_index = len(arr) // 2
		arr=arr[start_index:]
		hourly_precipitation_probability = hourly_precipitation_probability[start_index:]
	return arr, hourly_precipitation_probability

