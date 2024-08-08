import concurrent.futures
import time
from datetime import datetime
from os import path, mkdir
from typing import Union, Literal, Self

import numpy as np
import pandas as pd

from Day import Day

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser
from Parsers.OpenmeteoParser import OpenmeteoParser
from Parsers.SeekParser import SeekParser
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoSeeker import GismeteoSeeker
from Parsers.OpenmeteoSeeker import OpenmeteoSeeker

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


class Forecast:

    @classmethod
    def all_sources(cls):
        return ["Gismeteo", "Foreca", "Openmeteo"]

    def __init__(self, temp_sources=None, rainfall_sources=None, mode:Literal["Parser","Seeker"] = 'Seeker'):
        if temp_sources is None or len(temp_sources)==0:
            temp_sources = self.all_sources()
        if rainfall_sources is None: rainfall_sources = []
        self.temps = temp_sources
        self.rainfalls = rainfall_sources
        self.sources: list[BaseParser|SeekParser] = [globals()[f"{s}{mode}"]() for s in self.all_sources()]
        self.city = 'Лыткарино'

    def fetch_forecast(self, date: datetime) -> pd.DataFrame:
        combined = pd.DataFrame({"time": np.arange(0, 24)}, dtype=float)
        for getter in self.sources:
            forecast = getter.get_weather(date).add_prefix(getter.name + "_", axis=1)
            combined = pd.merge(combined, forecast, how="left", left_on="time", right_on=f"{getter.name}_time").drop(
                columns=f"{getter.name}_time")

        combined["mean_temp"] = combined.filter(regex=f'_temperature$').mean(axis=1)

        columns = ["time", "mean_temp"]
        for s in self.temps:
            columns.append(f"{s}_temperature")
        for s in self.rainfalls:
            columns.append(f"{s}_precipitation")

        combined = combined[columns]

        return combined

    def last_updated(self, date) -> datetime:
        dates = [getter.get_last_forecast_update(date) for getter in self.sources]
        print([s.name for s in self.sources], ":", dates)
        return min(dates)

    def load_new_data(self, date:datetime):
        # self.fetch_forecast(date)
        for getter in self.sources:
            getter.get_weather(date)
            time.sleep(0.2)
        print(datetime.now(), f"finished updating forecasts for {date.strftime('%d.%m.%Y')}")

    def find_city(self, city) -> Self:
        self.city = city
        for getter in self.sources:
            # print(f"{datetime.now()} started {getter.name}")
            getter.find_city(city)
            # print(f"{datetime.now()} finished {getter.name}")
        return self

    def change_sources(self, temp_sources=None, rainfall_sources=None) -> Self:
        if temp_sources is None or len(temp_sources)==0:
            temp_sources = self.all_sources()
        if rainfall_sources is None: rainfall_sources = []
        self.temps = temp_sources
        self.rainfalls = rainfall_sources
        return self

