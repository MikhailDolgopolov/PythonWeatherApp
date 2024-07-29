import locale
from datetime import datetime, timedelta, timezone
from typing import Union
from suntime import Sun

from helpers import inflect, my_point

locale.setlocale(locale.LC_TIME, 'ru_RU')


class Day:
    def __init__(self, offset: Union[0, 1]):
        self.date = datetime.today() + timedelta(days=offset)
        self.offset = offset
        self.day = self.date.strftime("%e")
        self.day_name = self.date.strftime("%A")
        self.accs_day_name = inflect(self.day_name, 'accs')
        self.D_month = f"{self.day} {inflect(self.date.strftime('%B').lower(), 'gent')}"
        self.short_date = self.date.strftime("%Y%m%d")
        self.full_date = self.date.strftime("%d-%m-%Y")
        self.forecast_name = f"{self.short_date}-{offset}"
        sun = Sun(*my_point())
        mid = self.date + timedelta(days=0.5)
        tz = timezone(timedelta(hours=3))
        suntime = [sun.get_sunrise_time(mid, tz), sun.get_sunset_time(mid, tz)]
        self.suntime = [d.hour + d.minute / 60 + d.second / 3600 for d in suntime]
