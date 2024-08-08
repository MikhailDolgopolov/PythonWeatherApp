import string
from pprint import pprint
from typing import List

import Levenshtein
import numpy as np
from geopy import Nominatim, Location
from geopy.exc import GeocoderTimedOut
from geopy.distance import distance


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


def get_closest_city_matches(input_name, max_results=3) -> list[Location]:
    geolocator = Nominatim(user_agent="city_name_detector")

    try:
        # Geocode the input to get potential city matches
        locations = geolocator.geocode(input_name,
                                       # country_codes='RU',
                                       addressdetails=True,
                                       language='ru',
                                       featuretype='city',
                                       exactly_one=False, limit=6)
        if locations is None:
            return []

        names = [loc.address.split(',')[0].lower() for loc in locations]
        ds = {locations[i].address: Levenshtein.distance(input_name.lower(), names[i]) for i in range(len(locations))}

        # Normalize the distances
        normalized_ds = {k: v / len(k.split(',')[0]) for k, v in ds.items()}
        # Filter results with normalized distance less than 0.2
        result = [k for k, v in ds.items() if normalized_ds[k] < 0.4]

        # Sort results by normalized distance
        result = sorted(result, key=lambda loc: normalized_ds[loc])

        # Retrieve the original Location objects based on the address
        final_results = [loc for loc in locations if loc.address in result][:max_results]
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


def find_closest_city(target_city: str, cities: List[str]) -> str|None:
    closest_city = cities[0]
    min_distance = float('inf')  # Initialize to a large number

    for city in cities:
        distance = distance_between_cities(city.translate(str.maketrans('', '', string.punctuation)), target_city)
        if distance < 15:
            return city
        if distance < min_distance:
            min_distance = distance
            closest_city = city

    if closest_city is None: closest_city=cities[0]
    if min_distance>15: return None
    return closest_city