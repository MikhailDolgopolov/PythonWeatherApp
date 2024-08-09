import datetime
import os.path
import threading
from typing import Self

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from Geography.Geography import find_closest_city
from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from Parsers.SeekParser import SeekParser
from helpers import random_delay


class GismeteoSeeker(SeekParser):
    def __init__(self, headless=True):
        self.__url = "https://www.gismeteo.ru/weather-lytkarino-12640/"
        super().__init__(name="Gismeteo", headless=headless)
        self.metadata = MetadataController(self.forecast_path)

    def _parse_page(self, date:datetime) -> BeautifulSoup | None:
        today = datetime.datetime.today()
        if self.driver_down:
            print(f"{self.name} driver is down")
            return None
        random_delay()
        diff = (date.date() - today.date()).days
        if diff == 0:
            try:
                self.driver.find_element(By.XPATH, "/html/body/header/div[2]/div")
            except:
                print("Couldn't find the element")
                return None
            random_delay()

            return BeautifulSoup(self.driver.page_source, "lxml")
        else:
            try:
                for i in range(diff):
                    tomorrow = self.driver.find_element(By.XPATH, "/html/body/main/div[1]/section[2]/div/a[2]")
                    tomorrow.click()
                    random_delay(0.5, 2)
            except:
                return None
            return BeautifulSoup(self.driver.page_source, "lxml")

    def _parse_weather(self, date:datetime, path:str) -> pd.DataFrame | None:
        if self.driver_down:
            self.init_driver()
            self.driver.get(self.__url)

        soup = self._parse_page(date)
        if soup is None:
            print("Couldn't parse Gismeteo")
            super().close()
            return None
        self.metadata.update_with_now(date)
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
            loaded=None
            path = f"{self.forecast_path}/{date.strftime('%Y%m%d')}.csv"
            file_existed = os.path.isfile(path)
            if self.metadata.update_is_overdue(date) or not file_existed:
                loaded = self._parse_weather(date, path)
            elif self.metadata.update_is_due(date):
                threading.Thread(target=self._parse_weather, args=[date, path]).start()
            if file_existed:
                loaded = pd.read_csv(path, dtype=float)

        else:
            loaded = self._parse_weather(date, "")

        if not self.active: loaded = self.empty_frame
        if loaded is None:
            loaded = self.empty_frame
        loaded = loaded.set_index('time').reindex(np.arange(0, 24)).reset_index(drop=False).interpolate()
        return loaded

    def get_last_forecast_update(self, date: datetime) -> datetime:
        return self.metadata.get_last_update(date, self.home)

    def find_city(self, name:str) -> Self:
        self.home = "лыткарино" in name.lower()

        self.init_driver()
        self.driver.get(self.__url)
        if self.home or self._current_city == name:
            self.active = True
            return self
        super().find_city(name)

        random_delay()

        search = self.driver.find_element(By.CSS_SELECTOR, '.search-form input[type=text]')
        search.send_keys(name)

        try:
            try:
                random_delay(3, 4)
                answers_main = self.driver.find_elements(By.CSS_SELECTOR, ".search-item")[:2]
                random_delay(0,1)
                answers_info = self.driver.find_elements(By.CSS_SELECTOR, ".search-item span")[:2]

                names = [a.text.split()[0] for a in answers_main]
                regions = [a.text.split(" (")[0].split(', ',maxsplit=1)[-1].replace('\n', ' ') for a in answers_info]

                options = [f'{regions[i]}, {names[i]}'.replace('\n', ' ') for i in range(len(answers_main))]
                best = find_closest_city(name, options)
                random_delay()
                if best is None:
                    self.active = False
                    return self
                else:
                    self.active = True
                answer = self.driver.find_elements(By.CSS_SELECTOR, ".search-item")[options.index(best)]
            except:
                answer = self.driver.find_elements(By.CSS_SELECTOR, ".search-item")[0]
            answer.click()
            random_delay()
            return self
        except:
            raise RuntimeError(f"Something went wrong looking up {name}")

    def clean_files(self) -> int:
        return self.metadata.cleaning()

