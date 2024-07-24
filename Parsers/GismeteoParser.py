import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from Parsers.BaseParser import BaseParser
import time

class GismeteoParser(BaseParser):
    def __init__(self):
        self.__url = "https://www.gismeteo.ru/weather-lytkarino-12640/"
        super().__init__()

    def parse_page(self, date) -> BeautifulSoup | None:
        today = datetime.datetime.today()
        self.driver.get(self.__url)
        diff = (date.date()-today.date()).days
        if diff==0:
            return BeautifulSoup(self.driver.page_source, "lxml")
        if diff==1:
            try:
                tomorrow = self.driver.find_element(By.XPATH, "/html/body/main/div[1]/section[2]/div/a[2]")
            except:
                tomorrow = self.driver.find_element(By.XPATH, "/html/body/section[4]/section/nav/a[3]")
            tomorrow.click()
            return BeautifulSoup(self.driver.page_source, "lxml")
        else:
            print("Is not supported")

    def get_weather(self, date) -> dict:
        soup = self.parse_page(date)

        table = soup.find("div", "widget-items")
        times_row = table.find("div", "widget-row-datetime-time")
        clocks = [s.text.split(":")[0] for s in times_row.findAll("span")]
        cloudiness_row = table.find("div", "widget-row-icon")
        clouds = [d.get("data-tooltip") for d in cloudiness_row.findAll("div", "row-item")]
        temps_row = table.find("div", "chart")
        temps = [t.text for t in temps_row.findAll("temperature-value")]
        rain_row = table.find("div", "widget-row-precipitation-bars")
        mm_percp = [r.text for r in rain_row.findAll("div", "item-unit")]
        wind_row_items = table.find("div", "row-wind-gust").findAll("div", "row-item")
        wind = [list(w.strings) for w in wind_row_items]
        wind = [int(item) if item.isdigit() else 0 for sublist in wind for item in sublist]

        d = [[clocks[i],int(temps[i]), float(mm_percp[i].replace(",", ".")), wind[i]] for i in range(len(clouds))]
        # print(clocks)
        # print(clouds)
        # print(temps)
        # print(mm_percp)
        # print(wind)
        return d

