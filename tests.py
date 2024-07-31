from datetime import datetime

from ForecastRendering import get_and_render
from Parsers.ForecaParser import ForecaParser
from Parsers.GismeteoParser import GismeteoParser

# get_and_render(0,  False, True, True)
get_and_render(1,  False, True, True)

# ForecaParser().get_weather(datetime.today())

