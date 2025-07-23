import numpy as np
import matplotlib
from matplotlib import pyplot as plt, patches, lines
import seaborn as sns

from datetime import datetime

from scipy.stats import alpha

from Day import Day

plt.style.use('seaborn-v0_8-whitegrid')

WEATHER_CAT = {
    **dict.fromkeys([0],           "clear"),
    **dict.fromkeys([1, 2, 3],    "partly_cloudy"),
    **dict.fromkeys([45, 48, 51, 53, 55, 61, 63, 65, 71, 73, 75, 95], "overcast"),
}
COLORS = {
    "clear":         "#fff5ba",
    "partly_cloudy": "#d0ebff",
    "overcast":      "#d3d3d3",
    "temp_line":     "#444444",
    "precipitation_amount": "#175fd4",
    "min_temp": "#50a5de",
    "max_temp": "#ba2b00",
    "sun_time": "#f2a200",
}


def render_forecast_data(data, date: datetime, city: str = None, save=True, uid: int = 0):
    day = Day(date)
    data = data.interpolate()

    # Agg backend if saving
    if save:
        matplotlib.use('Agg')

    fig, ax1 = plt.subplots(figsize=(8, 6))
    x = data["hour"]
    temps = data["temperature"]

    plot_bottom = temps.min()-5
    plot_top = temps.max()+1

    # — 1) condition bands —
    if "weathercode" in data:
        for hr, code in zip(x, data["weathercode"].astype(int)):
            cat = WEATHER_CAT.get(code, "overcast")
            ax1.axvspan(hr - 0.5, hr + 0.5,
                        facecolor=COLORS[cat], alpha=0.8, zorder=0)

    # — 3) temperature line —
    temp_line = ax1.plot(x, temps,
                         color=COLORS["temp_line"],
                         linewidth=2.5,
                         label="Температура, °C",
                         zorder=4)[0]

    # x-axis formatting
    ax1.set_xlim(-0.5, 23.5)
    ax1.set_xticks(range(0, 24, 2))
    ax1.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])
    ax1.set_xlabel("Часы")

    # — 4) precipitation bars (if any) —
    prec = data["precipitation"]
    has_prec = prec.rolling(window=2, center=True).mean().max() >= 0.5
    bar_bottom = plot_bottom + 0.5
    ax2 = ax1.twinx()
    if has_prec:

        ax2.bar(x, prec,
                            width=0.8,
                            # bottom=bar_bottom,
                            label="Осадки, мм",
                            color=COLORS["precipitation_amount"],
                            alpha=0.8,
                            zorder=3)
        ax2.hlines(0, -1,24, color=COLORS['temp_line'], alpha=0.8, zorder=0)

        ax2.set_ylabel("Осадки, мм", rotation=270, labelpad=15)
        ax2.grid(False)
        vis_prec_amt = max(3, prec.max())
        ax2.set_ylim(-vis_prec_amt*0.1, vis_prec_amt)
    else:
        ax2.text(12, bar_bottom, "Осадков не ожидается", ha='center', va='bottom', fontsize=16, alpha=0.6)  # Add a label

    sun_start, sun_end = day.suntime
    for xc in (sun_start, sun_end):
        ax1.vlines(xc, ymin=plot_bottom, ymax=plot_top,
                   color=COLORS['sun_time'], linestyle='dotted', linewidth=4, zorder=1)

    # — 5) min/max horizontal lines —
    lo_i, hi_i = int(temps.idxmin()), int(temps.idxmax())
    lo_t, hi_t = temps.min(), temps.max()
    ax1.hlines([lo_t, hi_t], -1, [lo_i, hi_i],
               linestyles="--",
               linewidth=1,
               colors=[COLORS['min_temp'], COLORS['max_temp']],
               zorder=2)

    handles = []
    labels = []

    y_min, y_max = ax1.get_ylim()
    # one tick per degree, rounded
    y_ticks = np.arange(np.floor(y_min), np.ceil(y_max), 1)
    ax1.set_yticks(y_ticks)


    # temp line
    handles.append(lines.Line2D([], [], color=COLORS['temp_line'], linewidth=2.5))
    labels.append("Темп., °C")

    # precipitation
    if has_prec:
        handles.append(patches.Patch(facecolor=COLORS['precipitation_amount'], alpha=0.8))
        labels.append("Осадки, мм")

        # Add sunrise/sunset line handle for legend
        handles.append(lines.Line2D([], [], color=COLORS['sun_time'], linestyle='dotted', linewidth=4))
        labels.append("Световой день")

    # weather conditions
    for cat in set(WEATHER_CAT.values()):
        handles.append(patches.Patch(facecolor=COLORS[cat], alpha=0.9))
        # human‑friendly label:
        name = {
            "clear": "Ясно",
            "partly_cloudy": "Облачно с прояснениями",
            "overcast": "Пасмурно"
        }[cat]
        labels.append(name)

    ax1.legend(handles, labels,
               loc="best",
               frameon=True,
               fontsize='medium',
               framealpha=0.93,
               handlelength=3,  # shorten line length
               handletextpad=0.5,  # tighter text
               borderpad=0.4,  # reduce frame padding
               labelspacing=0.4,  # less vertical space between entries
               borderaxespad=1)

    # grid, titles
    ax1.grid(True, linestyle=":", linewidth=1, alpha=1, zorder=0)
    ax1.text(x=12, y=plot_top+0.2, s=city or "", fontsize=12, ha="center", va="bottom")

    main_title = f"{day.accs_day_name}, {day.D_month}"
    ax1.set_title(f"Прогноз на {main_title}\n\n", fontsize=14, fontweight='bold', y=0.96)

    ax1.set_ylim(plot_bottom, plot_top)
    # save/show
    path = f"Images/{day.short_date}_{uid}.png"
    if save:
        fig.savefig(path, bbox_inches="tight", dpi=400)
    else:
        plt.show()

    plt.close(fig)
    return {"path": path, "day": day}
