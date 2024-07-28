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

    def __init__(self, forecast: Forecast, day: Day):
        self.colormap = {"Foreca": "green", "Gismeteo": "blue", "OpenMeteo": "red"}
        self.day = day
        full_data = forecast.fetch_forecast(day)
        columns = full_data.columns.drop(["precipitation-probability"])
        factors_set = set()
        for col in columns:
            before, after = col.split('_', 1)
            factors_set.add(after)

        self.factors = list(factors_set)
        self.time = full_data.index
        self.__dict = {
            self.source_names[i]: full_data.loc[:, full_data.columns.str.startswith(self.source_names[i].lower())]
            .rename(columns=lambda x: x.split("_")[1]) for i in range(len(self.source_names))}
        self.precipitation_probability = full_data["precipitation-probability"]

        cols = full_data.filter(regex=r'_precipitation$')
        each = cols.sub(cols.mean(axis=1), axis=0).abs()
        diffs = each.mean(axis=1)
        # stds = full_data.filter(regex=r'_precipitation$').fillna(0).std(axis=1)

        probable = np.clip(self.precipitation_probability, 0, 20)
        b = np.max(diffs)
        if b != 0:
            self.precp_certainty = 1-0.6 * np.arctan(diffs)
        else:
            self.precp_certainty = diffs * 0
        print("Data, 47: unnecessary calculations")
        self.mean_values = {}
        for suffix in self.factors:
            selected_columns = full_data.filter(regex=f'_{suffix}$')
            self.mean_values[suffix] = selected_columns.mean(axis=1)

        prec_count = np.count_nonzero(self.mean_values["precipitation"])
        prob_count = np.count_nonzero(np.where(self.precipitation_probability > 1, 1, 0)) * 100
        prec_per_hour = 0 if prec_count == 0 else sum(self.mean_values["precipitation"]) / prec_count
        prob_per_hour = 0 if prob_count == 0 else sum(self.precipitation_probability) / prob_count
        self.precipitation_exists = prob_per_hour * prec_per_hour > 0.007
        if day.offset == 0:
            pd.DataFrame(data=self.mean_values).to_csv(path_or_buf=f"{os.getcwd()}/archive/{day.short_date}.csv", index_label="time",
                                                       index=True)

    def get_one(self, index):
        return self.__dict[self.source_names[index]]

    def get_source(self, name):
        return self.__dict[name]
