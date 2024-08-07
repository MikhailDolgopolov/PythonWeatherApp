import os.path
import random
import threading
import time
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from Parsers.SeekParser import SeekParser
from helpers import random_delay


class ForecaSeeker(SeekParser):
    def __init__(self):
        self.__url = "https://www.foreca.ru/Russia/Lytkarino"
        super().__init__(name="Foreca", headless=False)
        self.metadata = MetadataController(self.forecast_path)

    def _parse_date(self, date) -> BeautifulSoup | None:
        detail = date.strftime("%Y%m%d")
        url = self.driver.current_url + "?details=" + detail
        try:
            self.driver.get(url)
            random_delay()
            source = self.driver.page_source
            if self.home: self.metadata.update_with_now(date)
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
        if self.home: df.to_csv(path, index=False)
        return df

    def get_weather(self, date: datetime) -> pd.DataFrame:
        if not self.home: self._parse_weather(date, "")
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

    def find(self, name:str):
        if not name: return self
        self.home = name.lower() == "лыткарино"
        self.init_driver()
        self.driver.get(self.__url)

        #/html/body/div[2]/div/header/div[1]/div/div/form/input[1]

        search = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/header/div[1]/div/div/form/input[1]')
        search.send_keys(name)
        random_delay()
        try:
            answer = self.driver.find_elements(By.CLASS_NAME, "result-row")[0]
            random_delay()
            answer.click()
            random_delay(2,4)
            return self
        except:
            raise RuntimeError(f"Something went wrong looking up {name}")