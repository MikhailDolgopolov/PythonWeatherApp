from pprint import pprint

import pandas as pd


class ForecastData:

    @property
    def source_names(self):
        return ["Foreca", "Gismeteo", "OpenMeteo"]

    def __init__(self, full_data: pd.DataFrame):
        columns = full_data.columns.drop(["precipitation-probability"])
        sources_set = set()
        factors_set = set()
        for col in columns:
            before, after = col.split('_', 1)
            sources_set.add(before)
            factors_set.add(after)
        # self.sources = list(sources_set)
        self.factors = list(factors_set)
        self.time = full_data.index
        self.__dict = {
            self.source_names[i]: full_data.loc[:, full_data.columns.str.startswith(self.source_names[i].lower())]
                .rename(columns=lambda x: x.split("_")[1]) for i in range(len(self.source_names))}
        self.precipitation_probability = full_data["precipitation-probability"]

        self.mean_values = {}

        for suffix in self.factors:
            selected_columns = full_data.filter(regex=f'_{suffix}$')
            self.mean_values[suffix] = selected_columns.mean(axis=1)

        # print(pd.DataFrame(mean_values))

    def get_one(self, index):
        return self.__dict[self.source_names[index]]
