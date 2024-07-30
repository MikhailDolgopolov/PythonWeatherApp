import time
from datetime import datetime, timedelta
import random

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium_stealth import stealth
import pickle


class BaseParser:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("start-maximized")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--incognito")
        options.add_argument("--disable-plugins-discovery")

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        self.driver: WebDriver = webdriver.Chrome(options=options)
        stealth(self.driver,
                languages=["ru-Ru", "ru"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        try:
            for cookie in pickle.load(open("cookies.pkl", "rb")):
                self.driver.add_cookie(cookie)
        except FileNotFoundError:
            pass

    def close(self):
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))

    def get_weather(self, date) -> pd.DataFrame:
        raise NotImplementedError("Subclasses should implement this method")

    def get_weather_today(self) -> pd.DataFrame:
        return self.get_weather(datetime.now())

    def get_weather_tomorrow(self) -> pd.DataFrame:
        return self.get_weather(datetime.now() + timedelta(days=1))

    def close(self):
        self.driver.close()
        self.driver.quit()
