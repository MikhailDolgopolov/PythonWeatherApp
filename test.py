from pprint import pprint

import pandas as pd

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from helpers import read_json

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters

from Parsers.OpenMeteo import get_open_meteo
from Parsers.ForecaParser import ForecaParser
import re
from datetime import datetime

# mishad2304+python@gmail.com
# dolgpa+python@gmail.com
# midolgop@yandex.ru





# for s in addresses:
#     print(re.search(pattern, s).group(1))