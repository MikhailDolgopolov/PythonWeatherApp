import time
from datetime import datetime, timedelta
import random

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium_stealth import stealth
import pickle


class BaseParser:
    def __init__(self, *args):
        self.__options = webdriver.ChromeOptions()
        # self.__options.add_argument("--headless")
        self.__options.add_argument("start-maximized")

        self.__options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.__options.add_experimental_option('useAutomationExtension', False)
        self.__options.add_argument("disable-infobars")
        self.__options.add_argument("--disable-extensions")
        self.__options.add_argument("--profile-directory=Default")
        self.__options.add_argument("--incognito")
        self.__options.add_argument("--disable-plugins-discovery")

        self.__user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
                "Opera/9.80 (Windows NT 10.0; Win64; x64) Presto/2.12.388 Version/12.18",]
        self.__renderers = ["Intel Iris OpenGL Engine",
                            "Intel(R) UHD Graphics 620",
                            "NVIDIA GeForce GTX 1050 Ti",
                            "AMD Radeon RX 580",
                            "Intel(R) HD Graphics 4000",
                            "NVIDIA GeForce RTX 2080",
                            "AMD Radeon Vega 8 Graphics", ]

        self.init_driver(*args)

    def init_driver(self, *args):
        print(datetime.now(), "Started driver", *args)
        self.__options.add_argument(f"user-agent={random.choice(self.__user_agents)}")
        self.driver: WebDriver = webdriver.Chrome(self.__options)
        stealth(self.driver,
                languages=["ru-Ru", "ru"],
                vendor="Google Inc.",
                platform="Win64",
                webgl_vendor="Intel Inc.",
                renderer=random.choice(self.__renderers),
                fix_hairline=True,
                )
        try:
            for cookie in pickle.load(open("cookies.pkl", "rb")):
                self.driver.add_cookie(cookie)
        except FileNotFoundError:
            pass
        except:
            print("Couldn't add cookies")

    def close(self):
        try:
            pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        except:
            pass
        self.driver.quit()
        print(datetime.now(), "closed driver")

    def get_weather(self, date) -> pd.DataFrame:
        raise NotImplementedError("Subclasses should implement this method")

    def get_weather_today(self) -> pd.DataFrame:
        weather = self.get_weather(datetime.now())
        self.close()
        return weather

    def get_weather_tomorrow(self) -> pd.DataFrame:
        weather = self.get_weather(datetime.now() + timedelta(days=1))
        self.close()
        return weather

