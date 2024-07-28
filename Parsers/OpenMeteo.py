import numpy as np
import openmeteo_requests

import requests_cache
import pandas as pd
from matplotlib import pyplot as plt
from retry_requests import retry

from helpers import my_point

# Set up the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"


def get_open_meteo(day=1)->tuple[np.array, np.array]:
    print("Loading OpenMeteo...")
    p = my_point()
    params = {
        "latitude": p[0],
        "longitude": p[1],
        "hourly": ["temperature_2m", "precipitation_probability", "precipitation", "wind_speed_10m"],
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
    hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()

    h = np.arange(0, 24)
    if day == 2:
        h = np.arange(-24, 24)
    arr = np.array([h, hourly_temperature_2m, hourly_precipitation, hourly_wind_speed_10m]).T
    if day == 2:
        start_index = len(arr) // 2
        arr = arr[start_index:]
        hourly_precipitation_probability = hourly_precipitation_probability[start_index:]
    return arr, hourly_precipitation_probability
