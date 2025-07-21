
from typing import List

from geopy import Nominatim, Location
from geopy.exc import GeocoderTimedOut
from geopy.distance import distance

city_types = [
    'suburb', 'neighbourhood', 'city', 'village', 'town', 'residential',
    'hamlet', 'locality', 'isolated_dwelling', 'farm',
    'administrative', 'state', 'region', 'county', 'province', 'district'
]


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
        locations = geolocator.geocode(
            input_name,
            addressdetails=True,
            language='ru',
            exactly_one=False,
            limit=10
        )
        if not locations:
            return []

        # Prioritize locations by type
        prioritized = sorted(
            locations,
            key=lambda loc: (
                loc.raw.get('type') in ['city', 'town', 'village'],
                loc.raw.get('type') in city_types,
                loc.raw.get('importance', 0)
            ),
            reverse=True
        )

        # Deduplicate (by rounded coords)
        seen = set()
        unique_locations = []
        for loc in prioritized:
            identifier = (round(loc.latitude, 3), round(loc.longitude, 3))
            if identifier not in seen:
                seen.add(identifier)
                unique_locations.append(loc)

        return unique_locations[:max_results]

    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return []


def distance_between_places(point: str, target: str) -> float:
    geolocator = Nominatim(user_agent="city_name_detector")

    try:
        start = geolocator.geocode(
            point,
            addressdetails=True,
            language='ru'
        )
        end = geolocator.geocode(
            target,
            addressdetails=True,
            language='ru'
        )

        if start and end:
            return distance(
                (start.latitude, start.longitude),
                (end.latitude, end.longitude)
            ).km
        return float('inf')  # Unreachable
    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return float('inf')


def what_is_there(point: str | tuple) -> Location | None:
    geolocator = Nominatim(user_agent="place_finder")
    try:
        locations = geolocator.reverse(
            point,
            addressdetails=True,
            language='ru',
            exactly_one=False
        )
        if not locations:
            return None

        # Prefer places with a name and higher importance
        places = sorted(
            locations,
            key=lambda loc: (bool(loc.raw['address'].get('city') or loc.raw['address'].get('state')),
                             loc.raw.get('importance', 0)),
            reverse=True
        )
        return places[0]
    except GeocoderTimedOut:
        print("Geocoding service timed out.")
        return None
