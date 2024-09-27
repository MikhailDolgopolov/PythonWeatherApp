from datetime import datetime, timedelta


import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from helpers import my_point

# Set up the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below


class OpenmeteoParser(BaseParser):
    def __init__(self):
        super().__init__(name="Openmeteo")
        self.__url = "https://api.open-meteo.com/v1/forecast"
        # print("Loading OpenMeteo...")
        self.set_params()

        response = openmeteo.weather_api(self.__url, params=self.__params)[0]
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ), "temperature_2m": hourly_temperature_2m, "precipitation": hourly_precipitation,
            "wind_speed_10m": hourly_wind_speed_10m}

        df = pd.DataFrame(data=hourly_data)
        df["date"] = pd.to_datetime(df['date']).dt.tz_convert('Europe/Moscow')
        df = df.rename({"temperature_2m":"temperature", "wind_speed_10m":"wind-speed"}, axis=1)
        self.__full_dataframe = df
        self.__update_time = datetime.now()

    def set_params(self, p=None):
        if not p: p = my_point()
        self.__params = {
            "latitude": p[0],
            "longitude": p[1],
            "hourly": ["temperature_2m", "precipitation", "wind_speed_10m"],
            "wind_speed_unit": "ms",
            "timezone": "Europe/Moscow",
            "forecast_days": 8
        }

    def get_weather(self, date:datetime) -> pd.DataFrame:
        start_of_day = pd.Timestamp(date.date()).tz_localize('Europe/Moscow')
        end_of_day = start_of_day+pd.Timedelta(days=1)
        data = self.__full_dataframe[(self.__full_dataframe['date'] >= start_of_day) & (self.__full_dataframe['date'] < end_of_day)]
        data.insert(0, "time", data["date"].dt.hour)
        data = data.drop("date", axis=1).reset_index(drop=True)

        return data

    def get_last_forecast_update(self, date) -> datetime:
        return self.__update_time

