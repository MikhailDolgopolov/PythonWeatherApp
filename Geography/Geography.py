import string
from pprint import pprint
from typing import List

import Levenshtein
import numpy as np
from geopy import Nominatim, Location
from geopy.exc import GeocoderTimedOut
from geopy.distance import distance
from geopy.extra.rate_limiter import RateLimiter

city_types = ['suburb', 'neighbourhood', 'city', 'village', 'town', 'residential', 'administrative']

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

def get_location(address: str) -> Location|None:
    geolocator = Nominatim(user_agent="city_name_detector")

    try:
        # Geocode the input to get potential city matches
        location = geolocator.geocode(address,
                                       addressdetails=True,
                                       language='ru',
                                       )
        return location
    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return None

def get_closest_city_matches(input_name, max_results=6) -> list[Location]:
    geolocator = Nominatim(user_agent="city_name_detector")


    try:
        # Geocode the input to get potential city matches
        locations = geolocator.geocode(input_name,
                                       addressdetails=True,
                                       language='ru',
                                       featuretype='city',
                                       exactly_one=False, limit=6)
        if locations is None:
            return []
        locations = [loc for loc in locations if loc.raw['type'] in
                     city_types]
        seen = set()
        unique_locations = []

        for location in locations:
            # Use (latitude, longitude) as a unique identifier
            identifier = (round(location.latitude,1), round(location.longitude, 1))

            if identifier not in seen:
                seen.add(identifier)
                unique_locations.append(location)

        locations:list[Location] = unique_locations
        return locations[:max_results]

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
        if dist < threshold:
            return city
        if dist < min_distance:
            min_distance = dist
            closest_city = city

    if closest_city is None: closest_city=cities[0]
    if min_distance>threshold: return None
    return closest_city

def what_is_there(point: str|tuple) -> Location:
    geolocator = Nominatim(user_agent="place finder")

    try:
        # Geocode the input to get potential city matches
        locations = geolocator.reverse(point,
                                             addressdetails=True,
                                             language='ru',
                                             exactly_one=False
                                             )

        if len(locations)==1: return locations[0]
        max_importance, place = 0, locations[0]

        for l in locations:
            if l.raw["importance"]>max_importance:
                place = l
                max_importance = l.raw['importance']
        return place

    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return []