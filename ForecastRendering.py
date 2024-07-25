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
    result = (np.array(color1) * (1 - factor) + np.array(color2) * factor).astype(int)

    return result


def hex_to_rgb(hex_color):
    """
    Converts a hex color to an RGB tuple.
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb_color):
    """
    Converts an RGB tuple to a hex color.
    """
    return '#%02x%02x%02x' % tuple(rgb_color)


def render_forecast_data(data: ForecastData, sources: list[str] = None):
    if sources is None:
        sources = data.source_names

    structure = "".join(sorted([s.lower()[0] for s in sources]))
    sources.append("mean")

    fig, ax1 = plt.subplots(figsize=(6, 5))
    Xaxis = data.time
    main_plot = "temperature"
    for s in sources:
        if s == "mean": continue
        plt.plot(Xaxis, data.get_source(s)[main_plot], linestyle='-', color=data.colormap[s], label=s)
    if "mean" in sources:
        plt.fill_between(Xaxis, data.mean_values[main_plot] - 1, data.mean_values[main_plot] + 1, color=[0.5] * 4)
    ax1.set_xlabel("Время, ч")
    ax1.set_ylabel("Температура, °C")
    plt.legend()

    bottom = np.min(data.mean_values[main_plot]) - 3
    if not data.precipitation_exists:
        plt.ylim(bottom=bottom)
    if data.precipitation_exists:
        color1 = hex_to_rgb("#98cefa")  # Uncertain
        color2 = hex_to_rgb("#0026FF")  # Certain

        colors = [rgb_to_hex(interpolate_color(color1, color2, factor)) for factor in data.precp_certainty]
        bottom -= 5
        prob_height = 1  # height of the precipitation probability graph
        plt.bar(Xaxis, data.mean_values["precipitation"], color=colors, bottom=bottom)
        plt.fill_between(Xaxis, bottom, -prob_height * data.precipitation_probability / 100 + bottom,
                         color='#abebff')
        plt.plot(Xaxis, [bottom] * 24, color="black")

        ax2 = ax1.secondary_yaxis("right", functions=(lambda x: (x - bottom), lambda x: x - bottom))
        ax2.set_ylabel("Осадки, мм")

        ybottom, ytop = -prob_height + bottom, max(data.mean_values[main_plot]) + 6
        plt.ylim(bottom=ybottom)

        step = 3
        # print(plt.yticks())
        ybottom = int(ybottom) // step * step
        ytop = round(ytop // step) * step
        plt.yticks(np.arange(ybottom, ytop, step))

    plt.grid(which="both", color="lightgray")
    plt.xlim(0, 23)
    plt.xticks(Xaxis)

    first_tick = plt.yticks()[0][1]
    if not data.precipitation_exists and first_tick > 0:
        plt.plot(Xaxis, [first_tick] * 24, color="black")
    plt.title(f"Прогноз на {data.accs_name}", y=1.05)

    plt.savefig(f"Images/{my_filename(data.forecast_day)}-{structure}.png", bbox_inches="tight")
    plt.show()
    plt.close()
