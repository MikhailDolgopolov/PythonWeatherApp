import os
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from matplotlib import pyplot as plt
import seaborn as sns

from Day import Day
from Forecast import Forecast
from helpers import check_and_add_numbers

sns.set_style("whitegrid")
pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters


def render_forecast_data(forecast: Forecast, date: datetime, save=True, show=False, uid:int = 0):
    day = Day(date)
    data = forecast.fetch_forecast(date)
    print(f"Rendering for {day.full_date}")
    colormap = {"Foreca": "forestgreen", "Gismeteo": "blue", "Openmeteo": "orangered"}
    fig, ax1 = plt.subplots(figsize=(6, 5))
    x_axis = data["time"]

    temps = data.filter(regex="_temperature", axis=1)
    temp_labels = [n.split("_")[0] for n in temps.columns]
    rains = data.filter(regex="_precipitation", axis=1)
    rain_labels = [n.split("_")[0] for n in rains.columns]
    for i in range(len(temps.columns)):
        col = temps.columns[i]
        plot_line = data[col]
        if plot_line.isna().all():
            continue

        plt.plot(x_axis, plot_line, color=colormap[temp_labels[i]], label=temp_labels[i], zorder=4)

    plt.plot(x_axis, data["mean_temp"], color=[0.6] * 3, alpha=0.5, linewidth=25, zorder=2)

    sunspan = day.suntime
    plt.axvspan(sunspan[0], sunspan[1], alpha=0.3, color="#ebbf2f", zorder=0)
    ax1.set_xlabel("Время, ч")
    ax1.set_ylabel("Температура, °C")
    plt.legend()

    bottom = np.min(data["mean_temp"]) - 5

    mean_prec = rains.mean(axis=1)
    prec_count = np.count_nonzero(mean_prec)
    prec_per_hour = 0 if prec_count == 0 else sum(mean_prec) / prec_count
    precipitation_exists = prec_per_hour > 0.1 and len(rain_labels)>0

    if not precipitation_exists:
        plt.ylim(bottom=bottom)

    if precipitation_exists:
        bottom -= 4

        bar_width = 1 / len(rain_labels)
        shift = (len(rain_labels) - 1) * 0.5
        for i in range(len(rain_labels)):
            amount = data[rains.columns[i]]
            plt.bar(x_axis + bar_width * (i - shift), amount, bar_width, bottom=bottom,
                    color = colormap[rain_labels[i]], zorder=4, linewidth=0)

        plt.plot(x_axis, [bottom] * 24, color="black", zorder=5)

        ax2 = ax1.secondary_yaxis("right", functions=(lambda x: (x - bottom), lambda x: x - bottom))
        ax2.set_ylabel("Осадки, мм")

    d = data["mean_temp"]
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

    path = f"Images/{day.short_date}_{uid}.png"

    if save:
        plt.savefig(path, bbox_inches="tight", dpi=600)
    if show:
        plt.show()
    plt.close()
    return {"path": path, "day": day}
