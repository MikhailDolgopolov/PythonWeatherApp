import json
from datetime import datetime, timedelta


def my_filename(day, truncated=False):
    if truncated:
        return f"{(datetime.today() + timedelta(days=day - 1)).strftime('%Y%m%d')}"
    return f"{(datetime.today()+timedelta(days=day-1)).strftime('%Y%m%d')}-{('today' if day==1 else 'tomorrow')}"

def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data
