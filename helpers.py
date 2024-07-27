import json
from datetime import datetime, timedelta
from typing import Union

import numpy as np
from pymorphy3 import MorphAnalyzer


morph = MorphAnalyzer()


def my_point():
    return 55.57, 35.91

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


def check_and_add_numbers(arr, nums, tolerance=1):
    result = list(arr)
    to_add=[]
    for num in nums:
        differences = np.abs(arr - num)
        closest_index = np.argmin(differences)

        if np.any(differences < tolerance):
            result[closest_index] = num
        else:
            to_add.append(num)

    result.extend(to_add)
    return np.array(result)

