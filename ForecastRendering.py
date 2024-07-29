import os
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from matplotlib import pyplot as plt
import seaborn as sns

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from helpers import check_and_add_numbers

sns.set_style("whitegrid")
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


def get_and_render(offset, save_image=True, show=False, generate_new=False):

    day = Day(offset)
    path = f"Images/{day.forecast_name}.png"
    if os.path.isfile(path) and not generate_new:
        return {"path": path, "day": day}
    else:
        forecast = Forecast()
        data = ForecastData(forecast, day)
        return render_forecast_data(data, save=save_image, show=show)


def render_forecast_data(data: ForecastData, save=True, show=False) -> dict[str, str | Day]:
    sources = data.source_names

    day = data.day
    print(f"Rendering for {day.full_date}")

    fig, ax1 = plt.subplots(figsize=(6, 5))
    x_axis = data.time
    main_plot = "temperature"
    for s in sources:
        plt.plot(x_axis, data.get_source(s)[main_plot], color=data.colormap[s], label=s, zorder=4)

    plt.plot(x_axis, data.mean_values[main_plot], color=[0.6]*3, alpha=0.5, linewidth=25, zorder=2)

    sunspan = day.suntime
    plt.axvspan(sunspan[0], sunspan[1], alpha=0.3, color="#ebbf2f", zorder=0)
    ax1.set_xlabel("Время, ч")
    ax1.set_ylabel("Температура, °C")
    plt.legend()

    bottom = np.min(data.mean_values[main_plot]) - 5
    if not data.precipitation_exists:
        plt.ylim(bottom=bottom)
    if data.precipitation_exists:
        bottom -= 4

        bar_width = 0.33
        for i in range(len(sources)):
            amount = np.array(data.get_source(sources[i])["precipitation"])
            plt.bar(x_axis+bar_width*(i-1), amount, bar_width, bottom=bottom, color=data.colormap[sources[i]], zorder=4, linewidth=0)

        plt.plot(x_axis, [bottom] * 24, color="black", zorder=5)

        ax2 = ax1.secondary_yaxis("right", functions=(lambda x: (x - bottom), lambda x: x - bottom))
        ax2.set_ylabel("Осадки, мм")

    d = data.mean_values[main_plot]
    lower_x = np.argmin(d)
    higher_x = np.argmax(d)
    lower_y = round(d[lower_x])
    higher_y = round(d[higher_x])
    plt.hlines([lower_y, higher_y], [0, 0], [lower_x, higher_x], linestyle=(5, (10, 3)), color=[0.3] * 3, linewidth=1,
               zorder=3)
    ticks = plt.yticks()[0]
    ticks = check_and_add_numbers(ticks, [lower_y, higher_y])
    plt.yticks(ticks)

    plt.grid(which="both", color="lightgray")
    plt.xlim(0, 23)
    plt.xticks(x_axis)
    plt.title(f"Прогноз на {day.accs_day_name}, {day.D_month}", y=1.05)

    path = f"Images/{day.forecast_name}.png"

    if save:
        plt.savefig(path, bbox_inches="tight", dpi=600)
    if show:
        plt.show()
    plt.close()
    return {"path": path, "day": day}

