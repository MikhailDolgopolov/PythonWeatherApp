from pprint import pprint

from bs4 import BeautifulSoup
import requests
from collections import defaultdict

from DailyWeather import DailyWeather

url = "https://www.foreca.ru/Russia/Lytkarino"
page = requests.get(url)


# Parse HTML
soup = BeautifulSoup(page.text, 'html.parser')

headers=soup.findAll("h4")
days= [h.text for h in soup.findAll("h4")]

day1, day2 = DailyWeather(days[0]), DailyWeather(days[1])

print(type(headers[0]))
