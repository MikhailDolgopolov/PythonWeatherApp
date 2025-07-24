import numpy as np
import matplotlib
from matplotlib import pyplot as plt, patches, lines
import seaborn as sns

from datetime import datetime
from Day import Day

plt.style.use('seaborn-v0_8-whitegrid')

WEATHER_CAT = {
    **dict.fromkeys([0],           "clear"),
    **dict.fromkeys([1, 2, 3],    "partly_cloudy"),
    **dict.fromkeys([45, 48, 51, 53, 55, 61, 63, 65, 71, 73, 75, 95], "overcast"),
}
COLORS = {
    "clear":             "#fff5ba",
    "partly_cloudy":     "#d0ebff",
    "overcast":          "#d3d3d3",
    "temp_line":         "#444444",
    "precipitation_amount": "#175fd4",
    "min_temp":          "#50a5de",
    "max_temp":          "#ba2b00",
    "sun_time":          "#f2a200",
}


def render_forecast_data(data, date: datetime, city: str = None, save=True, uid: int = 0):
    day = Day(date)
    data = data.interpolate()

    if save:
        matplotlib.use('Agg')

    fig, ax1 = plt.subplots(figsize=(8, 6))
    # give extra bottom space for legend
    fig.subplots_adjust(bottom=0.20)

    x = data["hour"]
    temps = data["temperature"]

    plot_bottom = temps.min() - 4
    plot_top    = temps.max() + 1

    # 1) condition bands
    if "weathercode" in data:
        for hr, code in zip(x, data["weathercode"].astype(int)):
            cat = WEATHER_CAT.get(code, "overcast")
            ax1.axvspan(hr - 0.5, hr + 0.5,
                        facecolor=COLORS[cat], alpha=0.8, zorder=0)

    # 2) temperature line
    ax1.plot(x, temps,
             color=COLORS["temp_line"],
             linewidth=2.5,
             label="Температура, °C",
             zorder=4)

    ax1.set_xlim(-0.5, 23.5)
    ax1.set_xticks(range(0, 24, 2))
    ax1.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])
    ax1.set_xlabel("Часы")

    # 3) precipitation bars
    prec = data["precipitation"]
    has_prec = prec.rolling(window=2, center=True).mean().max() >= 0.5
    ax2 = ax1.twinx()
    vis = max(3, prec.max())
    if has_prec:
        ax2.bar(x, prec,
                width=0.8,
                label="Осадки, мм",
                color=COLORS["precipitation_amount"],
                alpha=0.8,
                zorder=3)
        ax2.hlines(0, -1, 24,
                   color=COLORS["temp_line"], alpha=0.8, zorder=0)
        ax2.set_ylabel("Осадки, мм", rotation=270, labelpad=15)
        ax2.grid(False)

    else:
        ax2.text(12, 0, "Осадков не ожидается",
                 ha='center', va='bottom',
                 fontsize=16, alpha=0.6)
        ax2.set_axis_off()
    ax2.set_ylim(-0.05 * vis, vis*1.15)

    # 4) sun lines
    sun_start, sun_end = day.suntime
    for xc in (sun_start, sun_end):
        ax1.vlines(xc, ymin=plot_bottom, ymax=plot_top,
                   color=COLORS['sun_time'],
                   linestyle='dotted', linewidth=4, zorder=1)

    # 5) min/max lines
    lo_i, hi_i = int(temps.idxmin()), int(temps.idxmax())
    lo_t, hi_t = temps.min(), temps.max()
    ax1.hlines([lo_t, hi_t], -1, [lo_i, hi_i],
               linestyles="--", linewidth=1,
               colors=[COLORS['min_temp'], COLORS['max_temp']],
               zorder=2)

    # 6) y‑ticks
    y_min, y_max = ax1.get_ylim()
    yt = np.arange(np.floor(y_min), np.ceil(y_max), 1)
    ax1.set_yticks(yt)
    ax1.set_ylabel("Температура, °C")

    # 7) legend handles
    handles, labels = [], []

    # temp
    handles.append(lines.Line2D([], [], color=COLORS['temp_line'], linewidth=2.5))
    labels.append("Температура, °C")

    # sun
    handles.append(lines.Line2D([], [], color=COLORS['sun_time'],
                                linestyle='dotted', linewidth=4))
    labels.append("Световой день")

    # precip
    if has_prec:
        handles.append(patches.Patch(facecolor=COLORS['precipitation_amount'], alpha=0.8))
        labels.append("Осадки, мм")
    else:
        handles.append(patches.Patch(alpha=0))
        labels.append("")



    # conditions
    for cat in set(WEATHER_CAT.values()):
        handles.append(patches.Patch(facecolor=COLORS[cat], alpha=0.9))
        labels.append({"clear":"Ясно","partly_cloudy":"Обл. с прояснениями","overcast":"Пасмурно"}[cat])

    # 8) place legend below in 2 columns
    ax1.legend(handles, labels,
               loc='upper center',
               bbox_to_anchor=(0.5, -0.08),
               ncol=2,
               frameon=True,
               fontsize='medium',
               handlelength=3,
               handletextpad=0.5,
               borderpad=0.4,
               labelspacing=0.4,
               borderaxespad=0.5)

    # 9) grid & titles
    ax1.grid(True, linestyle=":", linewidth=1, alpha=1, zorder=0)
    ax1.text(12, plot_top+0.2, city or "",
             fontsize=12, ha="center", va="bottom")
    main_title = f"{day.accs_day_name}, {day.D_month}"
    ax1.set_title(f"Прогноз на {main_title}\n\n",
                  fontsize=14, fontweight='bold', y=0.96)

    ax1.set_ylim(plot_bottom, plot_top)

    # 10) save/show
    path = f"Images/{day.short_date}_{uid}.png"
    if save:
        fig.savefig(path, bbox_inches="tight", dpi=400)
    else:
        plt.show()

    plt.close(fig)
    return {"path": path, "day": day}
