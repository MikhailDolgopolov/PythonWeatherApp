import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


class ForecastRendering:
    def __init__(self, full_data:pd.DataFrame):
        columns = full_data.columns.drop("time")
        sources_set = set()
        factors_set = set()
        for col in columns:
            before, after = col.split('_', 1)
            sources_set.add(before)
            factors_set.add(after)
        sources = list(sources_set)
        factors = list(factors_set)

