from datetime import datetime
from typing import Self

import pandas as pd
from geopy.distance import geodesic

from Geography.CityNames import default_city
from Geography.Place import Place
from Parsers.OpenmeteoParser import OpenmeteoParser

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


class Forecast:
    def __init__(self):
        self.parser:OpenmeteoParser = OpenmeteoParser()
        self.place = Place(default_city)

    def fetch_forecast(self, date: datetime) -> pd.DataFrame:
        return self.parser.get_weather(date)

    def last_updated(self, date) -> datetime:
        return self.parser.get_last_forecast_update(date)

    def find_city(self, city: str) -> Self:
        self.place.set_new_location(city)
        self.parser.find_city(city)
        return self

    def point_info(self, point_tuple):
        point_tuple = tuple(float(num) for num in point_tuple.split(","))
        d = geodesic(self.place.coords, point_tuple).kilometers
        return round(d, 1)

    def set_openmeteo_point(self, point_tuple):
        point_tuple = tuple(float(num) for num in point_tuple.split(","))
        self.place.set_new_point(point_tuple)
        self.parser.set_params(point_tuple)
