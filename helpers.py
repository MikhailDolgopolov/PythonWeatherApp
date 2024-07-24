from datetime import datetime, timedelta


def my_filename(day):
    return f"{(datetime.today()+timedelta(days=day-1)).strftime('%Y%m%d')}-{('today' if day==1 else 'tomorrow')}"