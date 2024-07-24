import pandas as pd
import numpy as np
import math as m
from matplotlib import pyplot as plt
import seaborn as sns
sns.set_style("whitegrid")

from ForecastData import ForecastData
from helpers import my_filename

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters

def interpolate_color(color1, color2, factor):
    """
    Interpolates between two colors with a given factor.
    color1, color2: Colors to interpolate between (as RGB tuples).
    factor: Interpolation factor (0 = color1, 1 = color2).
    """
    result=(np.array(color1) * (1 - factor) + np.array(color2) * factor).astype(int)

    return result

def hex_to_rgb(hex_color):
    """
    Converts a hex color to an RGB tuple.
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color):
    """
    Converts an RGB tuple to a hex color.
    """
    return '#%02x%02x%02x' % tuple(rgb_color)


class ForecastRendering:
    def __init__(self, cs=None):
        if cs is None:
            cs = ["green", "blue", "red"]
        self.colors = cs

    def show_data(self, data: ForecastData):
        fig, ax1 = plt.subplots(figsize=(7,6))
        Xaxis = data.time
        main_plot = "temperature"
        for i in range(len(self.colors)):
            plt.plot(Xaxis, data.get_one(i)[main_plot],linestyle='-',  color=self.colors[i], label=data.source_names[i])
        ax1.set_xlabel("Время, ч")
        ax1.set_ylabel("Температура, °C")
        plt.legend()
        color1 = hex_to_rgb("#abebff")  # Uncertain
        color2 = hex_to_rgb("#0026FF")  # Certain

        colors = [rgb_to_hex(interpolate_color(color1, color2, factor)) for factor in data.precp_certainty]
        bottom = np.min(data.mean_values[main_plot])-8
        prob_height = 1 # height of the precipitation probability graph
        plt.bar(Xaxis, data.mean_values["precipitation"], color=colors, bottom=bottom)
        plt.fill_between(Xaxis, bottom, -prob_height*data.precipitation_probability/100+bottom, color='#abebff')
        plt.plot(Xaxis, [bottom]*24, color="black")
        plt.plot(Xaxis, [bottom]*24, color="black")

        ax2 = ax1.secondary_yaxis("right", functions=(lambda x: (x-bottom), lambda x: x-bottom))
        ax2.set_ylabel("Осадки, мм")

        ybottom, ytop = -prob_height+bottom, max(data.mean_values[main_plot])+6
        plt.xlim(0,23)
        plt.ylim(bottom=ybottom)
        plt.grid(which="both", color="lightgray")
        plt.xticks(Xaxis)

        step = 3
        ybottom = int(ybottom)//step*step
        ytop = round(ytop//step)*step
        plt.yticks(np.arange(ybottom, ytop, step))

        plt.savefig(f"Images/{my_filename(data.forecast_day)}.png")
        plt.show()
        plt.close()

        # plt.figure(figsize=(8, 6))  # Set the figure size
        # plt.plot(Xaxis, data.mean_values["temperature"])
        # plt.show()


