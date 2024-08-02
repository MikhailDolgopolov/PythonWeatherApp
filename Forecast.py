import concurrent.futures
import time
from os import path, mkdir

import numpy as np
import pandas as pd

from Day import Day

from MetadataController import MetadataController
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser


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
        print(f"With async={asnc} gathering weather has taken {end - start} seconds")

        openmeteo = nested_forecast[2][0]
        prob = pd.DataFrame({"time": openmeteo["time"], "precipitation-probability": nested_forecast[2][1]})
        foreca, gis = nested_forecast[0], nested_forecast[1]

        foreca = foreca.rename(columns=lambda x: x if x == "time" else "foreca_" + x)
        gis = gis.rename(columns=lambda x: x if x == "time" else "gismeteo_" + x)
        openmeteo = openmeteo.rename(columns=lambda x: x if x == "time" else "openmeteo_" + x)

        combined = pd.merge(foreca, openmeteo, on="time", how="outer")
        combined = pd.merge(combined, gis, on="time", how="left")
        combined = pd.merge(combined, prob, on="time")
        combined = combined.interpolate(method="linear")
        combined = combined.set_index("time")

        return combined

    def update_forecast(self, combined: pd.DataFrame, day:Day) -> pd.DataFrame:
        print("updating old values...")
        gis = self.__gismeteo.get_weather(day.date)
        o_meteo, prob = get_open_meteo(day.offset + 1)
        fore = self.__foreca.get_weather(day.date)

        combined = combined.drop(labels=list(combined.filter(regex="gismeteo_", axis=1).columns), axis=1)
        fs = ["temperature", "precipitation", "wind-speed"]
        for s in fs:
            combined[f"openmeteo_{s}"] = o_meteo[s]
            combined[f"foreca_{s}"] = combined[f"foreca_{s}"].combine_first(fore[s])

        gis = gis.rename(columns=lambda x: x if x == "time" else "gismeteo_" + x)
        combined = pd.merge(combined, gis, on="time", how="left")
        combined["precipitation_probability"] = prob
        combined = combined.interpolate(method="linear")
        combined = combined.set_index("time")
        return combined

    def fetch_forecast(self, day: Day) -> pd.DataFrame:
        update = False
        if MetadataController.update_is_due(day) or MetadataController.update_is_overdue(day):
            update = True
        folder = "forecast"
        filename = f"{folder}/{day.forecast_name}.csv"
        if path.exists(folder):
            if path.exists(filename):
                combined = pd.read_csv(filename, dtype=np.float64, index_col="time")
                if update:
                    combined = self.update_forecast(combined, day)
                    combined.to_csv(path_or_buf=filename, index_label="time", index=True)
                    MetadataController.update_with_now(day)
                    print(f"updated data saved at '{filename}'")
                else:
                    print(f"found saved data for {day.full_date}")
                return combined
            else:
                print(f"no saved data found for {day.full_date}")
        else:
            print(f"no saved data found for {day.full_date}")
            mkdir(folder)
        data = self.get_pandas(day)
        data.to_csv(path_or_buf=filename, index_label="time", index=True)
        MetadataController.update_with_now(day)
        print(f"new data saved at '{filename}'")
        return data

    def finish(self):
        self.__foreca.close()
        self.__gismeteo.close()
