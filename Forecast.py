
import time
from datetime import datetime

from typing import Literal, Self

import numpy as np
import pandas as pd

from Geography.Geography import get_coordinates
from geopy.distance import geodesic




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

    def __init__(self, temp_sources=None, rain_sources=None, mode:Literal["Parser","Seeker"] = 'Seeker'):
        self.parsers:list[BaseParser | SeekParser] = []
        self.temps:list[str] = []
        self.rains:list[str] = []
        print("Forecast init")
        self.city = 'Лыткарино, Московская область'
        self.city_coords = get_coordinates(self.city)
        if temp_sources is None: temp_sources=self.all_sources()
        if rain_sources is None: rain_sources=self.all_sources()
        self.change_temp_sources(temp_sources, mode)
        self.change_rain_sources(rain_sources, mode)
        print("Forecast object is ready")

    def fetch_forecast(self, date: datetime) -> pd.DataFrame:
        combined = pd.DataFrame({"time": np.arange(0, 24)}, dtype=float)
        for getter in self.parsers:
            forecast = getter.get_weather(date)
            # print(forecast)
            forecast = forecast.add_prefix(getter.name + "_", axis=1)
            combined = pd.merge(combined, forecast, how="left", left_on="time", right_on=f"{getter.name}_time").drop(
                columns=f"{getter.name}_time")

        combined["mean_temp"] = combined.filter(regex=f'_temperature$').mean(axis=1)

        columns = ["time", "mean_temp"]
        for s in self.temps:
            columns.append(f"{s}_temperature")
        for s in self.rains:
            columns.append(f"{s}_precipitation")

        combined = combined[columns]

        return combined

    def last_updated(self, date) -> datetime:
        dates = [getter.get_last_forecast_update(date) for getter in self.parsers]
        #print([s.name for s in self.parsers], ":", dates)
        return min(dates)

    def load_new_data(self, date:datetime):
        for getter in self.parsers:
            getter.get_weather(date)
            time.sleep(0.2)
        print(datetime.now(), f"finished updating forecasts for {date.strftime('%d.%m.%Y')}")

    def find_city(self, city:str) -> Self:
        self.city = city
        self.city_coords = get_coordinates(city)
        for i in range(len(self.parsers)):
            getter = self.parsers[i]
            getter.find_city(city)
        return self

    def change_temp_sources(self, new_temp_sources:list[str], mode:Literal["Parser","Seeker"] = 'Seeker') -> Self:
        old_sources = list({*self.temps, *self.rains})
        new_sources = list({*new_temp_sources, *self.rains})

        missing_sources = [source for source in new_sources if source not in old_sources]
        for source in missing_sources:
            new_parser = globals()[f"{source}{mode}"]()
            new_parser.find_city(self.city)
            self.parsers.append(new_parser)

        self.temps = new_temp_sources
        parsers_to_remove = [p for p in self.parsers if p.name not in new_sources]
        for odd in parsers_to_remove:
            self.parsers.remove(odd)

        return self
    
    def change_rain_sources(self, new_rain_sources:list[str], mode:Literal["Parser", "Seeker"] = 'Seeker') -> Self:
        old_sources = list({*self.temps, *self.rains})
        new_sources = list({*self.temps, *new_rain_sources})

        missing_sources = [source for source in new_sources if source not in old_sources]
        for source in missing_sources:
            new_parser = globals()[f"{source}{mode}"]()
            new_parser.find_city(self.city)
            self.parsers.append(new_parser)

        self.rains = new_rain_sources
        parsers_to_remove = [p for p in self.parsers if p.name not in new_sources]
        for odd in parsers_to_remove:
            self.parsers.remove(odd)

        return self

    def clear_files(self):
        deleted = 0
        for s in self.parsers:
            deleted += s.clean_files()
        if deleted>0:
            print(f"Cleanup deleted {deleted} files")


    def point_info(self, point_tuple):
        point_tuple = tuple(float(num) for num in point_tuple.split(","))
        for parser in self.parsers:
            if parser.name=="Openmeteo":
                # print(f"{self.city}: {self.city_coords}")
                # print(f"point: {point_tuple}")
                d = geodesic(self.city_coords, point_tuple).kilometers
                # print(f"dist: {d} km")
                return round(d,1)
        else:
            return "У вас не выбрано Openmeteo для прогноза по координатам"

    def set_openmeteo_point(self, point_tuple):

        point_tuple = tuple(float(num) for num in point_tuple.split(","))
        for parser in self.parsers:
            if parser.name == "Openmeteo":
                parser: OpenmeteoParser = parser
                parser.set_params(point_tuple)
        else:
            return "У вас не выбрано Openmeteo для прогноза по координатам"



