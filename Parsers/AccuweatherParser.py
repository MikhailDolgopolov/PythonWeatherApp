from datetime import datetime

import pandas as pd
import requests

from Parsers.BaseParser import BaseParser
from helpers import read_json


class AccuweatherParser(BaseParser):
    def __init__(self, city="Лыткарино"):
        super().__init__(name="Accuweather", use_selenium=False)
        print("Loading AccuWeather...")
        self.__api_key = read_json("secrets.json")["accuweather"]
        self.city = city
        self.__location_key=0

    def find_location_key(self):
        base_url = "http://dataservice.accuweather.com/locations/v1/cities/search"

        params = {
            'apikey': self.__api_key,
            'q': self.city,
            'language': 'ru-ru'
        }

        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            locations = response.json()
            if locations:
                self.__location_key = locations[0]['Key']
                self.city = locations[0]["LocalizedName"]
                return self.__location_key
            else:
                raise ValueError("City not found")
        else:
            response.raise_for_status()

    def get_json(self):
        if self.__location_key == 0: raise UserWarning("Location wasn't specified or found")
        base_url = "http://dataservice.accuweather.com/forecasts/v1/daily/120hour/"
        url = f"{base_url}{self.__location_key}"

        params = {
            'apikey': self.__api_key,
            'metric': 'true',
            'language': 'ru-ru',
            'details':'true'
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def load_weather(self):
        data = self.get_json()
        array = data["DailyForecasts"]

        day1 = array[0]
        print(day1["Temperature"])