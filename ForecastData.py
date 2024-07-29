import os
from pprint import pprint

import numpy as np
import pandas as pd

from datetime import datetime, timedelta

from Day import Day
from Forecast import Forecast


class ForecastData:

    @property
    def source_names(self):
        return ["Foreca", "Gismeteo", "OpenMeteo"]

    def __init__(self, forecast: Forecast, day: Day, update_forecast=False):
        self.colormap = {"Foreca": "green", "Gismeteo": "blue", "OpenMeteo": "red"}
        self.day = day
        full_data = forecast.fetch_forecast(day, update_forecast)
        columns = full_data.columns.drop(["precipitation-probability"])
        # print(full_data.columns)
        # print(full_data["precipitation-probability"])
        factors_set = set()
        for col in columns:
            before, after = col.split('_', 1)
            factors_set.add(after)

        self.factors = list(factors_set)
        self.time = full_data.index
        self.__dict = {
            self.source_names[i]: full_data.loc[:, full_data.columns.str.startswith(self.source_names[i].lower())]
            .rename(columns=lambda x: x.split("_")[1]) for i in range(len(self.source_names))}

        self.mean_values = {}
        for suffix in self.factors:
            selected_columns = full_data.filter(regex=f'_{suffix}$')
            self.mean_values[suffix] = selected_columns.mean(axis=1)

        prec_count = np.count_nonzero(self.mean_values["precipitation"])
        prob_count = np.count_nonzero(np.where(full_data["precipitation-probability"] > 2, 1, 0)) * 100
        prec_per_hour = 0 if prec_count == 0 else sum(self.mean_values["precipitation"]) / prec_count
        prob_per_hour = 0 if prob_count == 0 else sum(full_data["precipitation-probability"]) / prob_count
        self.precipitation_exists = prob_per_hour * prec_per_hour > 0.01
        if day.offset == 0:
            pd.DataFrame(data=self.mean_values).to_csv(path_or_buf=f"{os.getcwd()}/archive/{day.short_date}.csv", index_label="time",
                                                       index=True)

    def get_source(self, name):
        return self.__dict[name]
