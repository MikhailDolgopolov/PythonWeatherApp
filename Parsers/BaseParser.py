from datetime import datetime, timedelta

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver


class BaseParser:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver: WebDriver = webdriver.Chrome(options=options)
        # self.driver.maximize_window()

    def get_weather(self, date) -> pd.DataFrame:
        raise NotImplementedError("Subclasses should implement this method")

    def get_weather_today(self) -> pd.DataFrame:
        return self.get_weather(datetime.now())

    def get_weather_tomorrow(self) -> pd.DataFrame:
        return self.get_weather(datetime.now() + timedelta(days=1))

    def close(self):
        self.driver.close()
        self.driver.quit()
