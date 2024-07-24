
import numpy as np

from Forecast import Forecast


class ForecastData:

    @property
    def source_names(self):
        return ["Foreca", "Gismeteo", "OpenMeteo"]

    def __init__(self, forecast:Forecast, day:int):
        self.forecast_day=day
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

        self.mean_values = {}
        stds = full_data.filter(regex=r'_precipitation$').fillna(0).std(axis=1)
        b = np.max(stds)
        if b!=0:
            self.precp_certainty = 0.666 * np.arctan(7 * stds / b)
        else:
            self.precp_certainty = stds*0

        for suffix in self.factors:
            selected_columns = full_data.filter(regex=f'_{suffix}$')
            self.mean_values[suffix] = selected_columns.mean(axis=1)

        # full_data["precipitation-probability"] = np.array([90]*24)
        self.precipitation_probability = full_data["precipitation-probability"]
        print("precp probabilities are wrong")

    def get_one(self, index):
        return self.__dict[self.source_names[index]]
