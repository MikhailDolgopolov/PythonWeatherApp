import json
import os
import time
import random
from typing import Union

import numpy as np
from pymorphy3 import MorphAnalyzer

morph = MorphAnalyzer()


def my_point():
    return 55.57, 35.91


def read_json(file_path) -> dict:
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Current working directory:", os.getcwd(), "no file ", file_path)


def write_json(data: dict, path: str):
    with open(path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def inflect(word, case: Union["accs", "gent"]) -> str:
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


def random_delay(start=1, end=5):
    time.sleep(random.uniform(start, end))

