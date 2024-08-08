from datetime import datetime, timedelta
from pprint import pprint

from Forecast import Forecast
from Geography.Geography import verify_city, get_closest_city_matches
from Parsers.ForecaSeeker import ForecaSeeker
from Parsers.GismeteoParser import GismeteoParser
from Parsers.GismeteoSeeker import GismeteoSeeker

input_string = "Тамбов"

cities = get_closest_city_matches(input_string)
forecast = Forecast(mode="Seeker")
if not cities:
    print("Not found ", input_string)
else:
    city = cities[0].raw["name"]

    seeker = ForecaSeeker()
    seeker.find(city)
    # forecast.find_city(city)

    # print(forecast.city)