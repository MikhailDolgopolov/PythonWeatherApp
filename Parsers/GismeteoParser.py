import datetime
import random
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from helpers import random_delay


class GismeteoParser(BaseParser):
    def __init__(self):
        self.__url = "https://www.gismeteo.ru/weather-lytkarino-12640/"
        super().__init__(name="Gismeteo")
        self.metadata = MetadataController(self.forecast_path)

    def parse_page(self, date:datetime) -> BeautifulSoup | None:
        today = datetime.datetime.today()
        self.driver.get(self.__url)
        random_delay(4, 8)
        diff = (date.date() - today.date()).days
        if diff == 0:
            try:
                self.driver.find_element(By.XPATH, "/html/body/header/div[2]/div")
            except:
                print("Couldn't find the element")
                return None
            random_delay()
            self.metadata.update_with_now(date)
            return BeautifulSoup(self.driver.page_source, "lxml")
        else:
            try:
                for i in range(diff):
                    tomorrow = self.driver.find_element(By.XPATH, "/html/body/main/div[1]/section[2]/div/a[2]")
                    tomorrow.click()
                    random_delay(0.5, 2)
            except:
                return None
            self.metadata.update_with_now(date)
            return BeautifulSoup(self.driver.page_source, "lxml")

    def get_weather(self, date:datetime) -> pd.DataFrame:
        print("Loading Gismeteo...")
        soup = self.parse_page(date)
        if soup is None:
            print("Couldn't parse Gismeteo")
            super().close()
            return pd.DataFrame({"time":[], "temperature":[], "precipitation":[], "wind-speed":[]}).astype(float)
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
        return pd.DataFrame.from_records(data, columns=["time", "temperature", "precipitation", "wind-speed"]).astype(
            float)

    def get_last_forecast_update(self, date:datetime) -> datetime:
        return self.metadata.get_last_update(date)
