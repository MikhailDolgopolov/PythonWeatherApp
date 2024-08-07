import datetime
import threading

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from Parsers.SeekParser import SeekParser
from helpers import random_delay


class GismeteoSeeker(SeekParser):
    def __init__(self):
        self.__url = "https://www.gismeteo.ru/"
        super().__init__(name="Gismeteo", headless=False)
        self.metadata = MetadataController(self.forecast_path)

    def parse_page(self, date:datetime) -> BeautifulSoup | None:
        today = datetime.datetime.today()
        random_delay(4, 8)
        diff = (date.date() - today.date()).days
        if diff == 0:
            try:
                self.driver.find_element(By.XPATH, "/html/body/header/div[2]/div")
            except:
                print("Couldn't find the element")
                return None
            random_delay()
            if self.home: self.metadata.update_with_now(date)
            return BeautifulSoup(self.driver.page_source, "lxml")
        else:
            try:
                for i in range(diff):
                    tomorrow = self.driver.find_element(By.XPATH, "/html/body/main/div[1]/section[2]/div/a[2]")
                    tomorrow.click()
                    random_delay(0.5, 2)
            except:
                return None
            # self.metadata.update_with_now(date)
            if self.home: self.metadata.update_with_now(date)
            return BeautifulSoup(self.driver.page_source, "lxml")

    def _parse_weather(self, date:datetime, path:str) -> pd.DataFrame | None:
        print("Loading Gismeteo...")
        if self.driver_down: self.init_driver()
        soup = self.parse_page(date)
        if soup is None:
            print("Couldn't parse Gismeteo")
            super().close()
            return None
        table = soup.find("div", "widget-items")
        times_row = table.find("div", "widget-row-datetime-time")
        clocks = [s.text.split(":")[0] for s in times_row.findAll("span")]
        temps_row = table.find("div", "chart")
        temps = [t.text for t in temps_row.findAll("temperature-value")]
        rain_row = table.find("div", "widget-row-precipitation-bars")
        mm_percp = [r.text for r in rain_row.findAll("div", "item-unit")]
        wind_row_items = table.find("div", "row-wind-gust").findAll("div", "row-item")
        wind = [list(w.strings) for w in wind_row_items]
        wind = [int(item) if item.isdigit() else 0 for sublist in wind for item in sublist]

        data = [[clocks[i], int(temps[i]), float(mm_percp[i].replace(",", ".")), wind[i]] for i in range(len(clocks))]

        super().close()
        df = pd.DataFrame.from_records(data, columns=["time", "temperature", "precipitation", "wind-speed"]).astype(
            float)
        if self.home: df.to_csv(path, index=False)
        return df

    def get_weather(self, date:datetime) -> pd.DataFrame:
        if self.home:
            path = f"{self.forecast_path}/{date.strftime('%Y%m%d')}.csv"
            if self.metadata.update_is_overdue(date):
                loaded = self._parse_weather(date, path)
            else:
                loaded = pd.read_csv(path, dtype=float)
            if self.metadata.update_is_due(date):
                threading.Thread(target=self._parse_weather, args=[date, path]).start()
            if loaded is None:
                loaded = pd.DataFrame({}, columns=["time", "temperature", "precipitation", "wind-speed"]).astype(float)

        else:
            loaded = self._parse_weather(date, "")
        loaded.set_index('time').reindex(np.arange(0, 24)).reset_index(drop=False).interpolate()
        return loaded

    def find(self, name:str):
        self.home = name.lower() == "лыткарино"
        self.init_driver()
        self.driver.get(self.__url)

        random_delay()

        search = self.driver.find_element(By.XPATH, '/html/body/header/div[2]/div/div[1]/div[1]/div/input')
        search.send_keys(name)
        random_delay()
        try:
            answer = self.driver.find_elements(By.CLASS_NAME, "search-item")[0]
            random_delay()
            answer.click()
            return self
        except:
            raise RuntimeError(f"Something went wrong looking up {name}")

