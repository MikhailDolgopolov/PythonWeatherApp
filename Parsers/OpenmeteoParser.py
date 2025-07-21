from datetime import datetime, timedelta
from typing import Self, List, Tuple

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from Geography.Geography import get_coordinates
from MetadataController import MetadataController
from Parsers.SeekParser import SeekParser
from helpers import my_point

# Set up the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below


class OpenmeteoParser(SeekParser):
    def __init__(
        self,
        latitude: float = None,
        longitude: float = None,
        timezone: str = "Europe/Moscow",
        hourly_vars: List[str] = None,
        daily_vars: List[str] = None,
        forecast_days: int = 8,
    ):
        super().__init__(name="Openmeteo")
        # initial point
        if latitude is None or longitude is None:
            latitude, longitude = my_point()
        self.timezone = timezone
        self.hourly_vars = hourly_vars or ["temperature_2m", "precipitation", "wind_speed_10m", 'weathercode']
        self.daily_vars = daily_vars or ["sunrise", "sunset", "weathercode"]
        self.forecast_days = forecast_days

        self._set_base_params(latitude, longitude)
        self._last_reload: datetime = datetime.min
        self._full_df: pd.DataFrame = pd.DataFrame()
        # self._daily_df: pd.DataFrame = pd.DataFrame()
        self._reload_if_needed(force=True)

    def _set_base_params(self, lat: float, lon: float):
        self._params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": self.hourly_vars,
            "daily": self.daily_vars,
            "wind_speed_unit": "ms",
            "timezone": self.timezone,
            "forecast_days": self.forecast_days,
        }

    def _reload_if_needed(self, force: bool = False):
        """Reload from API if data is stale or forced."""
        stale_after = timedelta(hours=MetadataController.due())
        if force or (datetime.now() - self._last_reload) > stale_after:
            resp = openmeteo.weather_api(
                "https://api.open-meteo.com/v1/forecast",
                params=self._params
            )[0]
            self._parse_response(resp)
            self._last_reload = datetime.now()

    def _parse_response(self, resp):
        """Extract hourly & daily data into DataFrames."""

        # — Hourly —
        hourly = resp.Hourly()

        hourly_data = {"date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s"),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ).tz_localize(self.timezone)}

        # hourly_data["temperature_2m"] = hourly_temperature_2m

        for i, var in enumerate(self.hourly_vars):
            hourly_data[var] = hourly.Variables(i).ValuesAsNumpy()

        hr_df = pd.DataFrame(data=hourly_data)
        # rename columns to your simpler names
        hr_df = hr_df.rename(columns=lambda c: c
                             .replace("_2m", "")
                             .replace("wind_speed_10m", "wind_speed"))
        hr_df = hr_df.set_index("date")


        # stash
        self._full_df = hr_df

    def get_weather(self, date: datetime) -> pd.DataFrame:
        """
        Return the hourly data for the given date (0–23h).
        """
        self._reload_if_needed()
        day_start = pd.Timestamp(date.date(), tz=self.timezone)
        day_end = day_start + pd.Timedelta(days=1)
        # print(self._full_df)
        df = self._full_df.loc[day_start:day_end - pd.Timedelta(seconds=1)].copy()
        df["hour"] = df.index.hour
        return df.reset_index(drop=True)

    def get_last_forecast_update(self, date: datetime = None) -> datetime:
        return self._last_reload

    def set_params(self, p: Tuple[float, float] = None):
        """Manually update point & reload immediately."""
        if p is None:
            p = my_point()
        lat, lon = p
        self._set_base_params(lat, lon)
        self._reload_if_needed(force=True)

    def find_city(self, name: str) -> Self:
        """Lookup coords by name, update params & reload."""
        coords = get_coordinates(name)
        if coords:
            self._set_base_params(*coords)
            self._reload_if_needed(force=True)
        return self
