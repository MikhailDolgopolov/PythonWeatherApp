import random
import threading
import time
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser


class ForecaParser(BaseParser):
    def __init__(self):
        self.__url_template = "https://www.foreca.ru/Russia/Lytkarino?details="
        super().__init__(name="Foreca")
        self.metadata = MetadataController(self.forecast_path)

    def parse_date(self, date) -> BeautifulSoup | None:
        detail = date.strftime("%Y%m%d")
        url = self.__url_template + detail
        try:
            self.driver.get(url)
            time.sleep(random.uniform(5, 10))
            source = self.driver.page_source
            self.metadata.update_with_now(date)
            soup = BeautifulSoup(source, "lxml")
            super().close()
            return soup
        except Exception as ex:
            print(ex)
            return None

    def parse_weather(self, date) -> str:
        print("Loading Foreca...")
        soup = self.parse_date(date)
        if soup is None:
            print("Couldn't parse Foreca")

            return pd.DataFrame({"time":[], "temperature":[], "precipitation":[], "wind-speed":[]}).astype(float)
        table = soup.find("div", class_="hourContainer")
        data = [[row.find("span", "time_24h").text,
                 int(row.find("span", "temp_c").text),
                 row.find("span", "rain_mm").text.split()[0],
                 row.find("span", "wind_ms").text
                 ] for row in table.findAll("div", "hour")]
        df = pd.DataFrame.from_records(data,
                                         columns=["time", "temperature", "precipitation", "wind-speed"]).astype(float)
        super().close()
        path = f"{self.forecast_path}/{date.strftime('%Y%m%d')}.csv"
        df.to_csv(path_or_buf=path)
        return path

    def get_weather(self, date: datetime) -> pd.DataFrame:
        if self.metadata.update_is_overdue(date):
            path = self.parse_weather(date)
            if path is None:
                return pd.DataFrame({"time": [], "temperature": [], "precipitation": [], "wind-speed": []}).astype(
                    float)
            return pd.read_csv(path, dtype=float)
        path = f"{self.forecast_path}/{date.strftime('%Y%m%d')}.csv"
        if self.metadata.update_is_due(date):
            threading.Thread(target=self.parse_weather, args=[date]).start()
        return pd.read_csv(path, dtype=float)

    def get_last_forecast_update(self, date: datetime) -> datetime:
        return self.metadata.get_last_update(date)