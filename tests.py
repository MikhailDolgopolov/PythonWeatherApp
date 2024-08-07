from datetime import datetime, timedelta
from pprint import pprint

from Geography.Geography import verify_city
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker

city = "красноярск"

city = verify_city(city)
if not city: raise RuntimeError(city)
foreign = ForecaSeeker().find(city)
print(foreign.home)
data = foreign.get_weather(datetime.today()+timedelta(days=1))

print(data)