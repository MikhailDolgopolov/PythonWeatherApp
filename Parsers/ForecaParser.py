import os.path
import random
import threading
import time
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from helpers import random_delay


class ForecaParser(BaseParser):
    def __init__(self):
        self.__url_template = "https://www.foreca.ru/Russia/Lytkarino?details="
        super().__init__(name="Foreca")
        self.metadata = MetadataController(self.forecast_path)

    def _parse_date(self, date) -> BeautifulSoup | None:
        detail = date.strftime("%Y%m%d")
        url = self.__url_template + detail
        try:
            self.driver.get(url)
            random_delay()
            source = self.driver.page_source
            self.metadata.update_with_now(date)
            soup = BeautifulSoup(source, "lxml")
            return soup
        except Exception as ex:
            print(ex)
            return None

    def _parse_weather(self, date, path) -> pd.DataFrame | None:
        print("Loading Foreca...")
        if self.driver_down: self.init_driver()
        soup = self._parse_date(date)
        if soup is None:
            print("Couldn't parse Foreca")

            return None
        table = soup.find("div", class_="hourContainer")
        data = [[row.find("span", "time_24h").text,
                 int(row.find("span", "temp_c").text),
                 row.find("span", "rain_mm").text.split()[0],
                 row.find("span", "wind_ms").text
                 ] for row in table.findAll("div", "hour")]
        df = pd.DataFrame.from_records(data,
                                       columns=["time", "temperature", "precipitation", "wind-speed"]).astype(float)
        super().close()
        df.to_csv(path, index=False)
        return df

    def get_weather(self, date: datetime) -> pd.DataFrame:
        path = f"{self.forecast_path}/{date.strftime('%Y%m%d')}.csv"
        if not os.path.isfile(path) and date.date == datetime.today().date():
            return pd.DataFrame({"time": [], "temperature": [], "precipitation": [], "wind-speed": []}).astype(float)
        if self.metadata.update_is_overdue(date):
            return self._parse_weather(date, path)
        data = pd.read_csv(path, dtype=float)
        if self.metadata.update_is_due(date):
            threading.Thread(target=self._parse_weather, args=[date, path]).start()
        return data

    def get_last_forecast_update(self, date: datetime) -> datetime:
        return self.metadata.get_last_update(date)
