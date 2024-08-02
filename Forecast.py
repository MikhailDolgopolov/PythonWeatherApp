import concurrent.futures
import time
from datetime import datetime
from os import path, mkdir

import numpy as np
import pandas as pd

from Day import Day

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser
from Parsers.OpenmeteoParser import OpenmeteoParser


pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


class Forecast:
    def __init__(self, temp_sources=None, rainfall_sources=None):
        if temp_sources is None:
            temp_sources = ["Gismeteo", "Foreca", "Openmeteo"]
        if rainfall_sources is None: rainfall_sources=temp_sources
        self.temps = temp_sources
        self.rainfalls = rainfall_sources
        self.sources:list[BaseParser] = [globals()[f"{s}Parser"]() for s in ["Gismeteo", "Foreca", "Openmeteo"]]

    def fetch_forecast(self, date: datetime) -> pd.DataFrame:
        combined = pd.DataFrame({"time":np.arange(0,24)}, dtype=float)
        for getter in self.sources:
            forecast = getter.get_weather(date).add_prefix(getter.name+"_", axis=1)
            combined = pd.merge(combined, forecast, how="left", left_on="time", right_on=f"{getter.name}_time").drop(columns=f"{getter.name}_time")

        combined["mean_temp"] = combined.filter(regex=f'_temperature$').mean(axis=1)

        columns = ["time", "mean_temp"]
        for s in self.temps:
            columns.append(f"{s}_temperature")
        for s in self.rainfalls:
            columns.append(f"{s}_precipitation")

        print(columns)
        # print(list(combined.columns))
        # for c in columns:
        #     print(c in combined.columns)
        combined = combined[columns]

        return combined

    def last_updated(self, date)->datetime:
        dates = [getter.get_last_forecast_update(date) for getter in self.sources]
        return min(dates)


