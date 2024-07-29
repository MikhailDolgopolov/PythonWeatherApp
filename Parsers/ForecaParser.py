import pandas as pd
from bs4 import BeautifulSoup

from Parsers.BaseParser import BaseParser


class ForecaParser(BaseParser):
    def __init__(self):
        self.__url_template = "https://www.foreca.ru/Russia/Lytkarino?details="
        super().__init__()

    def parse_date(self, date) -> BeautifulSoup | None:
        detail = date.strftime("%Y%m%d")
        url = self.__url_template + detail
        try:
            self.driver.get(url)
            source = self.driver.page_source
            soup = BeautifulSoup(source, "lxml")
            return soup
        except Exception as ex:
            print(ex)
            return None

    def get_weather(self, date) -> pd.DataFrame:
        print("Loading Foreca...")
        soup = self.parse_date(date)
        table = soup.find("div", class_="hourContainer")
        data = [[row.find("span", "time_24h").text,
                 int(row.find("span", "temp_c").text),
                 row.find("span", "rain_mm").text.split()[0],
                 row.find("span", "wind_ms").text
                 ] for row in table.findAll("div", "hour")]
        data = pd.DataFrame.from_records(data,
                                         columns=["time", "temperature", "precipitation", "wind-speed"]).astype(float)
        return data
