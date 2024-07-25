from datetime import datetime, timedelta


def my_filename(day, truncated=False):
    if truncated:
        return f"{(datetime.today() + timedelta(days=day - 1)).strftime('%Y%m%d')}"
    return f"{(datetime.today()+timedelta(days=day-1)).strftime('%Y%m%d')}-{('today' if day==1 else 'tomorrow')}"