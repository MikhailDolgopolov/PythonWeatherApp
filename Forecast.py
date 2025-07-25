from datetime import datetime
from typing import Self, Tuple

import pandas as pd
from geopy.distance import geodesic

from Geography.CityNames import default_city
from Geography.Geography import get_closest_city_matches, what_is_there
from Geography.Place import Place
from Parsers.OpenmeteoParser import OpenmeteoParser

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


class Forecast:
    def __init__(self, starting_city: str = "Москва"):
        self._place = Place(starting_city)
        self.parser = OpenmeteoParser.from_place(self._place)

    @property
    def place_name(self) -> str:
        return self._place.display_name

    @property
    def current_place(self) -> Place:
        return self._place

    def change_current_place(self, place: Place):
        self._place = place

    def fetch_forecast(self, date: datetime) -> pd.DataFrame:
        return self.parser.get_weather(date)

    def last_updated(self, date: datetime = None) -> datetime:
        return self.parser.get_last_forecast_update(date)

    def find_city(self, city: str) -> Self:
        self._place = Place(city)
        self.parser.find_city(city)
        return self

    def new_point_info(self, coords: Tuple[float, float]) -> Tuple[Place, float]:
        self.parser.set_params(coords)
        place = Place(what_is_there(coords))
        return place, geodesic(self.current_place.coords, coords).km
