from os import path, mkdir

import numpy as np
import pandas as pd

from Day import Day
from helpers import read_json, write_json
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

    def get_raw_today(self):
        return self.__foreca.get_weather_today(), self.__gismeteo.get_weather_today(), get_open_meteo(1)

    def get_raw_tomorrow(self):
        return self.__foreca.get_weather_tomorrow(), self.__gismeteo.get_weather_tomorrow(), get_open_meteo(2)

    def get_raw_today_async(self):
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

    def get_pandas(self, day: Day, asnc=True):
        start = time.time()
        if asnc:
            nested_forecast = list(self.get_raw_today_async() if day.offset == 0 else self.get_raw_tomorrow_async())
        else:
            nested_forecast = list(self.get_raw_today() if day.offset == 0 else self.get_raw_tomorrow())
        end = time.time()
        metadata = read_json("metadata.json")
        min_date = datetime.today() - timedelta(days=1)
        max_date = datetime.today() + timedelta(days=1)
        new_meta = {k: v for k, v in metadata.items() if min_date < datetime.strptime(k, "%Y%m%d") < max_date}
        new_meta[day.short_date] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        write_json(new_meta, "metadata.json")
        print(f"With async={asnc} gathering weather has taken {end - start} seconds")

        for i in range(2):
            nested_forecast[i] = pd.DataFrame.from_records(nested_forecast[i],
                                                           columns=["time", "temperature", "precipitation",
                                                                    "wind-speed"]).astype(float)
        openmeteo = pd.DataFrame.from_records(nested_forecast[2][0], columns=["time", "temperature", "precipitation",
                                                                              "wind-speed"])
        prob = pd.DataFrame({"time": openmeteo["time"], "precipitation-probability": nested_forecast[2][1]})
        foreca, gis = nested_forecast[0], nested_forecast[1]

        # stregth = np.random.uniform(7, 18, size=3)
        # peak = np.random.uniform(6,18, size=3)
        # length = np.random.uniform(2,5, size=3)
        #
        # foreca["precipitation"]=np.exp(-np.power(np.arange(0,len(foreca))-peak[0],2)/length[0])*stregth[0]
        # gis["precipitation"]=np.exp(-np.power(np.arange(0,24,3)-peak[1],2)/length[1])*stregth[1]
        # openmeteo["precipitation"]=np.exp(-np.power(np.arange(0,24)-peak[2],2)/length[2])*stregth[2]

        foreca = foreca.rename(columns=lambda x: x if x == "time" else "foreca_" + x)
        gis = gis.rename(columns=lambda x: x if x == "time" else "gismeteo_" + x)
        openmeteo = openmeteo.rename(columns=lambda x: x if x == "time" else "openmeteo_" + x)

        combined = pd.merge(foreca, openmeteo, on="time", how="outer")
        combined = pd.merge(combined, gis, on="time", how="left")
        combined = pd.merge(combined, prob, on="time")
        combined = combined.interpolate(method="linear")
        combined = combined.set_index("time")

        return combined

    def fetch_forecast(self, day: Day, update=False) -> pd.DataFrame:
        folder = "forecast"
        filename = f"{folder}/{day.forecast_name}.csv"
        if path.exists(folder):
            if path.exists(filename):
                combined = pd.read_csv(filename, dtype=np.float64, index_col="time")

                print(f"found saved data for {day.full_date}")
                return combined
            else:
                print(f"no saved data found for {day.full_date}")
        else:
            print(f"no saved data found for {day.full_date}")
            mkdir(folder)
        data = self.get_pandas(day)
        data.to_csv(path_or_buf=filename, index_label="time", index=True)
        print(f"new data saved at '{filename}'")
        return data
