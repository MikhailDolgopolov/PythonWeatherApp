from datetime import datetime, timedelta
from pprint import pprint

from Geography.Geography import verify_city
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker


data = GismeteoParser().get_weather(datetime.today()+timedelta(days=7))

print(data)