import os.path
import random
import threading
import time
from datetime import datetime
from typing import Self

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from Geography.Geography import find_closest_city
from MetadataController import MetadataController
from Parsers.BaseParser import BaseParser
from Parsers.SeekParser import SeekParser
from helpers import random_delay


class ForecaSeeker(SeekParser):
    def __init__(self, headless=True):
        self.__url = "https://www.foreca.ru/Russia/Lytkarino"
        super().__init__(name="Foreca", headless=headless)
        self.metadata = MetadataController(self.forecast_path)

    def _parse_date(self, date) -> BeautifulSoup | None:
        detail = date.strftime("%Y%m%d")
        url = self.driver.current_url + "?details=" + detail
        try:

            self.driver.get(url)
            random_delay()
            source = self.driver.page_source
            soup = BeautifulSoup(source, "lxml")
            return soup
        except Exception as ex:
            print(ex)
            return None

    def _parse_weather(self, date, path) -> pd.DataFrame | None:
        # print("Loading Foreca...")
        if self.driver_down:
            self.init_driver()
            self.driver.get(self.__url)
        soup = self._parse_date(date)
        if soup is None:
            print("Couldn't parse Foreca")
            return None
        self.metadata.update_with_now(date)
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
            if not self.active: return self.empty_frame
            return pd.DataFrame({"time": [], "temperature": [], "precipitation": [], "wind-speed": []}).astype(float)
        if self.metadata.update_is_overdue(date):
            if not self.active: return self.empty_frame
            return self._parse_weather(date, path)
        data = pd.read_csv(path, dtype=float)
        if self.metadata.update_is_due(date):
            threading.Thread(target=self._parse_weather, args=[date, path]).start()

        if not self.active: return self.empty_frame
        return data

    def get_last_forecast_update(self, date: datetime) -> datetime:
        return self.metadata.get_last_update(date, self.home)

    def find_city(self, name:str) -> Self:
        self.home = "лыткарино" in name.lower()
        # t0 = time.time()
        self.init_driver()
        if self.home:
            self.driver.get("https://www.foreca.ru/Russia/Lytkarino")
            self.active = True
            return self
        self.driver.get(self.__url)

        #/html/body/div[2]/div/header/div[1]/div/div/form/input[1]

        try:
            random_delay(0.1, 0.5)
            try:
                #//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]
                button = self.driver.find_element(By.XPATH, "//*[@id='qc-cmp2-ui']/div[2]/div/button[2]")
                button.click()
                random_delay(0.1, 0.5)
                # print("Confidential click")
            except:
                # print("No button")
                pass
            random_delay(0.1, 0.5)
            #/html/body/div[3]/div/header/div[1]/div/div/form/input[1]
            #body > div.page-wrap > div > header > div.search-bar-inner > div > div > form > input[type=text]:nth-child(1)
            #div.search-bar-inner form>input[type=text]
            # search = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/header/div[1]/div/div/form/input[1]')
            search = self.driver.find_element(By.CSS_SELECTOR, "div.search-bar-inner form>input[type=text]")
            # print(search)
            search.send_keys(name)
            random_delay()
            try:
                answers = self.driver.find_elements(By.CLASS_NAME, "result-row")[:4]
                options = [a.text.replace('\n', ' ').split(' (')[0] for a in answers]
                best = find_closest_city(name, options)
                if best is None:
                    self.active = False
                    return self
                else:
                    self.active = True
                # print("best: ", best)
                random_delay()

                answer = self.driver.find_elements(By.CSS_SELECTOR, ".result-row")[options.index(best)]
            except:
                answer = self.driver.find_elements(By.CSS_SELECTOR, ".result-row")[0]
            answer.click()
            random_delay(0,1)
            # t1 = time.time()
            return self
        except:
            raise RuntimeError(f"Something went wrong looking up {name}")