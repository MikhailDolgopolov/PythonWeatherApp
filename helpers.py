import json
from datetime import datetime, timedelta
from typing import Union

from pymorphy3 import MorphAnalyzer


morph = MorphAnalyzer()


# def my_date(day: Union[int, Day]):
#     if isinstance(day, Day):
#         day = day.offset
#     return f"{(datetime.today() + timedelta(days=day - 1)).strftime('%Y%m%d')}"


# def my_filename(day):
#     return f"{my_date(day)}-{('today' if day == 1 else 'tomorrow')}"


def read_json(file_path):
    data = {}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except Exception as e:
        print(e)
    finally:
        return data


def write_json(data: dict, path: str):
    with open(path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def inflect(word, case: Union["accs", "gent"]) -> str:
    return morph.parse(word)[0].inflect({case}).word
