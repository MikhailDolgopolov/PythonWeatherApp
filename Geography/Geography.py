import string
from pprint import pprint
from typing import List

import Levenshtein
import numpy as np
from geopy import Nominatim, Location
from geopy.exc import GeocoderTimedOut
from geopy.distance import distance
from geopy.extra.rate_limiter import RateLimiter

from Geography.WeatherPlace import WeatherPlace
from helpers import is_cyrillic


def verify_city(name):
    geolocator = Nominatim(user_agent="city_locator for weather")
    location: Location = geolocator.geocode(name,
                                            country_codes='RU',
                                            addressdetails=True,
                                            language='ru',
                                            featuretype='city'
                                            )
    if location:
        return location.raw["name"]
    else:
        return None


def get_coordinates(name):
    geolocator = Nominatim(user_agent="city_locator for weather")
    location: Location = geolocator.geocode(name,
                                            country_codes='RU',
                                            addressdetails=True,
                                            language='ru',
                                            featuretype='city'
                                            )
    if location:
        return location.latitude, location.longitude
    return None


def get_closest_city(loc: Location) -> Location | None:
    geolocator = Nominatim(user_agent="city_name_detector")

    try:
        locations = geolocator.reverse(query=(loc.latitude, loc.longitude), addressdetails=True,
                                       language='ru', exactly_one=False)

        for location in locations:
            if location.raw['type'] in ['town', 'city']:
                return location
        for location in locations:
            address = location.raw['address']
            town=""
            if 'city' in address:
                town = f"{address['city']}, {address['country']}"
            elif 'town' in address:
                town = f"{address['town']}, {address['country']}"
            if town:
                return geolocator.geocode(town, addressdetails=True, language='ru')

    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return None


def get_closest_place_matches(input_name, max_results=4) -> list[WeatherPlace]:
    geolocator = Nominatim(user_agent="place_name_detector")

    try:
        # Geocode the input to get potential city matches
        locations = geolocator.geocode(input_name,
                                       addressdetails=True,
                                       language='ru',
                                       exactly_one=False, limit=max_results)
        if locations is None:
            return []
        print(len(locations))
        locations = [loc for loc in locations if loc.raw['type'] in
                     ['suburb', 'neighbourhood', 'city', 'village', 'hamlet', 'town', 'residential', 'administrative']]
        # print(f"3. {input_name}: {locations}")
        admins = [loc.raw['name'] for loc in locations if loc.raw['type'] == 'administrative']
        locations = [loc for loc in locations if not (loc.raw["type"] != 'administrative' and loc.raw['name'] in admins)]
        seen = set()
        unique_locations = []

        for location in locations:
            # Use (latitude, longitude) as a unique identifier
            identifier = (round(location.latitude*3, 1), round(location.longitude*3, 1))

            if identifier not in seen:
                seen.add(identifier)
                unique_locations.append(location)





        # Retrieve the original Location objects based on the address
        final_results: list[WeatherPlace] = [WeatherPlace(loc) for loc in locations]
        return final_results

    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return []


def distance_between_cities(point:str, target:str) ->float:
    geolocator = Nominatim(user_agent="city_name_detector")

    try:
        # Geocode the input to get potential city matches
        start:Location = geolocator.geocode(point,
                                       # country_codes='RU',
                                       addressdetails=True,
                                       language='ru',
                                       featuretype='city')
        end: Location = geolocator.geocode(target,
                                   # country_codes='RU',
                                   addressdetails=True,
                                   language='ru',
                                   featuretype='city')

        if start is None or end is None:
            return 20000

        return distance((start.latitude, start.longitude), (end.latitude, end.longitude)).km
    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return 20000


def find_closest_city(target_city: str, cities: List[str], threshold=15) -> str | None:
    closest_city = cities[0]
    min_distance = float('inf')  # Initialize to a large number

    for city in cities:
        dist = distance_between_cities(city, target_city)
        # print(f"{city:<40}, {distance}")
        if dist < threshold:
            return city
        if dist < min_distance:
            min_distance = dist
            closest_city = city

    if closest_city is None: closest_city=cities[0]
    if min_distance>threshold: return None
    return closest_city
