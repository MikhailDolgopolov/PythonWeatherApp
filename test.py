import email
import os
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pprint import pprint

import pandas as pd
from redmail import gmail

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from helpers import read_json

f = open("log.txt", "w")

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters

from Parsers.OpenMeteo import get_open_meteo
from Parsers.GismeteoParser import GismeteoParser
from Parsers.ForecaParser import ForecaParser
import re
from datetime import datetime

# p = GismeteoParser()
# pprint(p.get_weather_tomorrow())
pprint(get_open_meteo(1)[1])