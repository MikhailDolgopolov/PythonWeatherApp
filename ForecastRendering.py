from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use('Agg')
from matplotlib import pyplot as plt
import seaborn as sns

from Day import Day
from helpers import check_and_add_numbers

sns.set_style("whitegrid")
pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


def render_forecast_data(data:pd.DataFrame, date: datetime, city:str = None, save=True, show=False, uid:int = 0):
    day = Day(date)
    data = data.interpolate()
    print(f"Rendering for {day.full_date}")
    colormap = {"Foreca": "forestgreen", "Gismeteo": "blue", "Openmeteo": "orangered"}
    fig, ax1 = plt.subplots(figsize=(6, 5))
    x_axis = data["time"]

    temps = data['temperature']
    # temp_labels = [n.split("_")[0] for n in temps.columns]
    # rains = data.filter(regex="_precipitation", axis=1)
    # rain_labels = [n.split("_")[0] for n in rains.columns]

    plt.plot(x_axis, data['temperature'], color=colormap["Openmeteo"], label="Openmeteo", zorder=4)

    sunspan = day.suntime
    plt.axvspan(sunspan[0], sunspan[1], alpha=0.3, color="#ebbf2f", zorder=0)
    ax1.set_xlabel("Время, ч")
    ax1.set_ylabel("Температура, °C")
    plt.legend()

    bottom = np.min(temps) - 5

    mean_prec = data["precipitation"]
    prec_count = np.count_nonzero(mean_prec)
    prec_per_hour = 0 if prec_count == 0 else sum(mean_prec) / prec_count
    precipitation_exists = prec_per_hour > 0.1

    if not precipitation_exists:
        try:
            plt.ylim(bottom=bottom)
        except:
            print("Something strange with limits")
            bottom = np.min(data.filter(regex=f'_temperature$').mean(axis=1))

    if precipitation_exists:
        bottom -= 4

        bar_width = 1

        plt.bar(x_axis, mean_prec, bar_width, bottom=bottom,
                color=colormap["Openmeteo"], zorder=4, linewidth=0)
        plt.plot(x_axis, [bottom] * 24, color="black", zorder=5)

        ax2 = ax1.secondary_yaxis("right", functions=(lambda x: (x - bottom), lambda x: x - bottom))
        ax2.set_ylabel("Осадки, мм")

    lower_x = np.argmin(temps)
    higher_x = np.argmax(temps)
    lower_y = round(temps[lower_x])
    higher_y = round(temps[higher_x])
    plt.hlines([lower_y, higher_y], [0, 0], [lower_x, higher_x], linestyle=(5, (10, 3)), color=[0.4] * 3, linewidth=1,
               zorder=3)
    ticks = plt.yticks()[0]
    ticks = check_and_add_numbers(ticks, [lower_y, higher_y])
    plt.yticks(ticks)

    plt.grid(which="both", color="lightgray")
    plt.xlim(0, 23)
    plt.xticks(x_axis)
    plt.title(f"Прогноз на {day.accs_day_name}, {day.D_month}", y=1.07)
    if city: plt.suptitle(city, fontsize='medium', y=0.92)

    path = f"Images/{day.short_date}_{uid}.png"

    if save:
        plt.savefig(path, bbox_inches="tight", dpi=600)
    if show:
        plt.show()
    plt.close()
    return {"path": path, "day": day}
