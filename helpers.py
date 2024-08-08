import json
import os
import re
import time
import random
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from typing import Union, Literal

import numpy as np
from pymorphy3 import MorphAnalyzer

morph = MorphAnalyzer()


def my_point():
    return 55.58, 37.91


def read_json(json_path: Union[Path, str])->dict:
    if isinstance(json_path, str):
        json_path = Path(json_path)
    try:
        with json_path.open('r', encoding='utf-8') as file:
            return json.load(file)
    except:
        print(f"No file {json_path} in {os.getcwd()}")
        return {}


def write_json(data: dict, json_path: Union[Path, str])->None:
    if isinstance(json_path, str):
        json_path = Path(json_path)
    with json_path.open('w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def inflect(word, case: Literal["accs", "gent"]) -> str:
    return morph.parse(word)[0].inflect({case}).word


def check_and_add_numbers(arr, nums, tolerance=1):
    result = list(arr)
    to_add = []
    for num in nums:
        differences = np.abs(arr - num)
        closest_index = np.argmin(differences)

        if np.any(differences < tolerance):
            result[closest_index] = num
        else:
            to_add.append(num)

    result.extend(to_add)
    return np.array(result)


def random_delay(start=0.5, end=1):
    time.sleep(random.uniform(start, end))


def delete_old_files(folders):
    date = datetime.today() - timedelta(days=1)
    number = int(date.strftime("%Y%m%d"))
    to_delete = []
    for folder in folders:
        for file in glob(f'{folder}\\*.*'):
            match = re.search(r'\d+', file)
            if match and int(match.group()) < number:
                to_delete.append(file)
    for p in to_delete:
        os.remove(p)
    print(f"Removed {len(to_delete)} files.")
