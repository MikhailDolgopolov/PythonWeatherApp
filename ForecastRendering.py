import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

from ForecastData import ForecastData

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


class ForecastRendering:
    def __init__(self, cs=None):
        if cs is None:
            cs = ["green", "blue", "red"]
        self.colors = cs

    def show_data(self, data: ForecastData):
        plt.figure(figsize=(8, 6))  # Set the figure size
        Xaxis = data.time
        for i in range(len(self.colors)):
            plt.plot(Xaxis, data.get_one(i)["temperature"],linestyle='-',  color=self.colors[i], label=data.source_names[i])
        plt.grid(True)
        plt.legend()
        plt.show()
        plt.close()

        plt.figure(figsize=(8, 6))  # Set the figure size
        plt.plot(Xaxis, data.mean_values["temperature"])
        plt.show()


