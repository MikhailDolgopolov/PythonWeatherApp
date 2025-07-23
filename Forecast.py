from datetime import datetime
from typing import Self

import pandas as pd
from geopy.distance import geodesic

from Geography.CityNames import default_city
from Geography.Geography import get_closest_city_matches
from Geography.Place import Place
from Parsers.OpenmeteoParser import OpenmeteoParser

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


class Forecast:
    def __init__(self, starting_city: str = "Лыткарино, Московская область"):
        point = Place(starting_city)
        self.parser = OpenmeteoParser.from_place(point)
        self.place_name = point.display_name

    def fetch_forecast(self, date: datetime) -> pd.DataFrame:
        return self.parser.get_weather(date)

    def last_updated(self, date: datetime = None) -> datetime:
        return self.parser.get_last_forecast_update(date)

    def find_city(self, city: str) -> Self:
        self.place_name = city
        self.parser.find_city(city)
        return self

    def point_info(self, point_str: str) -> float:
        """Distance in km between current place and point_str='lat,lon'."""
        lat, lon = map(float, point_str.split(","))
        # you’ll need to store self.place_coords when find_city is called:
        src_coords = (self.parser._params["latitude"], self.parser._params["longitude"])
        return round(geodesic(src_coords, (lat, lon)).km, 1)

    def set_openmeteo_point(self, point_str: str):
        lat, lon = map(float, point_str.split(","))
        self.parser.set_params((lat, lon))
