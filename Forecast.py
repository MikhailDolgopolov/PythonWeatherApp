from os import path, mkdir

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser
from Parsers.OpenMeteo import get_open_meteo
import concurrent.futures
import time
from datetime import datetime, timedelta

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters

class Forecast:
    def __init__(self):

        self.__foreca = ForecaParser()
        self.__gismeteo = GismeteoParser()

        self.__names = ["Foreca", "Gismeteo", "OpenMeteo"]

    def get_raw_today(self):
        return self.__foreca.get_weather_today(), self.__gismeteo.get_weather_today(), get_open_meteo(1)

    def get_raw_tomorrow(self):
        return self.__foreca.get_weather_tomorrow(), self.__gismeteo.get_weather_tomorrow(), get_open_meteo(2)

    def get_raw_today_async(self):
        results = {}
        # Create a ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks to the executor
            foreca = executor.submit(self.__foreca.get_weather_today)
            gismeteo = executor.submit(self.__gismeteo.get_weather_today)
            openmeteo = executor.submit(get_open_meteo, 1)

        return foreca.result(), gismeteo.result(), openmeteo.result()

    def get_raw_tomorrow_async(self):
        # Create a ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks to the executor
            foreca = executor.submit(self.__foreca.get_weather_tomorrow)
            gismeteo = executor.submit(self.__gismeteo.get_weather_tomorrow)
            openmeteo = executor.submit(get_open_meteo, 2)

        return foreca.result(), gismeteo.result(), openmeteo.result()

    def get_pandas(self, day=2, asnc=True):
        start = time.time()
        if asnc:
            nested_forecast = list(self.get_raw_today_async() if day == 1 else self.get_raw_tomorrow_async())
        else:
            nested_forecast = list(self.get_raw_today() if day == 1 else self.get_raw_tomorrow())
        end = time.time()

        print(f"With async={asnc} gathering weather has taken {end - start} seconds")
        for i in range(len(nested_forecast)):
            nested_forecast[i] = pd.DataFrame.from_records(nested_forecast[i],
                                                           columns=["time", "temperature", "precipitation",
                                                                    "wind-speed"]).astype(float)
        return nested_forecast

    def fetch_forecast(self, day):
        date = datetime.today() + timedelta(days=day - 1)
        folder = "forecast"
        filename = f"{folder}/{date.strftime('%Y%m%d')}.csv"
        if path.exists(folder):
            if path.exists(filename):
                combined = pd.read_csv(filename, dtype=np.float64)
                print("saved data found")
                return combined
            else:
                print("no saved data found")
        else:
            print("no saved data found")
            mkdir(folder)
        nested = self.get_pandas(day)
        foreca, gis, openmeteo = nested
        gis = gis.rename(columns=lambda x: x if x=="time" else "gismeteo_" + x)
        data = {"time":openmeteo["time"]}
        cols = openmeteo.columns.drop("time")
        for s in range(0, 3, 2):
            for col in cols:
                data[f"{self.__names[s].lower()}_{col}"] = nested[s][col]
        combined = pd.DataFrame(data = data)
        combined = pd.merge(combined, gis, on="time", how="left")
        combined = combined.interpolate(method="linear")

        combined.to_csv(index=True, path_or_buf=filename)
        print(f"new data saved at '{filename}'")

    # def show(self, full_forecast):
    #     colors = ["green", "blue", "red"]
    #     plt.figure(figsize=(8, 6))  # Set the figure size
    #     data = self.get_pandas(day, asnc)
    #     for i in range(len(colors)):
    #         plt.plot(data[i]["time"], data[i]["temperature"], marker='o', linestyle='-', color=colors[i],
    #                  label=self.__names[i])
    #
    #     plt.grid(True)
    #     plt.legend()
    #     plt.show()
