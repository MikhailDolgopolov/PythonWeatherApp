
from typing import Union, Optional, Tuple, List

from geopy import Nominatim, Location
from geopy.exc import GeocoderTimedOut
from geopy.distance import distance

city_types = [
    'city', 'village', 'town',
    'hamlet', 'locality',
]

# Constants for configuration
TIMEOUT = 5  # seconds
MAX_RESULTS = 6
RU_COUNTRY_CODE = 'RU'
DEFAULT_LANGUAGE = 'ru'
USER_AGENT = "city_locator for weather" #Important to set a descriptive user agent.


def get_coordinates(name: str) -> Optional[Tuple[float, float]]:
    """Geocodes a name and returns coordinates if found."""
    geolocator = Nominatim(user_agent=USER_AGENT, timeout=TIMEOUT)
    try:
        location = geolocator.geocode(
            name,
            country_codes=RU_COUNTRY_CODE,
            addressdetails=True,
            language=DEFAULT_LANGUAGE,
            featuretype='city'  # Restrict to city-like features
        )
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except Exception as e:  #Catch broader exceptions for robustness
        print(f"Geocoding error in get_coordinates: {e}")
        return None


def get_location(address: str) -> Optional[Location]:
    """Geocodes an address and returns a Location object if found."""
    geolocator = Nominatim(user_agent=USER_AGENT, timeout=TIMEOUT)
    try:
        location = geolocator.geocode(address, addressdetails=True, language=DEFAULT_LANGUAGE)
        return location
    except Exception as e:
        print(f"Geocoding error in get_location: {e}")
        return None


def get_closest_city_matches(input_name: str, max_results: int = MAX_RESULTS) -> List[Location]:
    """Finds the closest city matches for an input name."""
    geolocator = Nominatim(user_agent=USER_AGENT, timeout=TIMEOUT)
    try:
        cities = geolocator.geocode(
            input_name,
            addressdetails=True,
            language=DEFAULT_LANGUAGE,
            exactly_one=False,
            limit=4,
            featuretype='city'
        )

        hamlets = geolocator.geocode(
            input_name,
            addressdetails=True,
            language=DEFAULT_LANGUAGE,
            exactly_one=False,
            limit=4,
            featuretype='settlement'
        )
        try:
            locations = cities + hamlets
            locations = [loc for loc in locations if loc is not None]
        except:
            return []

        prioritized = sorted(
            locations,
            key=lambda loc: (
                loc.raw.get('name') in input_name,
                loc.raw.get('type') in city_types and loc.raw.get('importance', 0) > 0,  #Prioritize cities with importance
                # loc.raw.get('distance'), #Sort by distance from the geocoder's default location
            ),
            reverse=True
        )

        # Deduplication (more robust - check for near duplicates)
        seen = set()
        unique_locations = []
        for loc in prioritized:
            skip=True
            for place_type in city_types:
                if place_type in loc.raw.get('address', []):
                    skip=False
                    break

            if skip:
                break
            identifier = (round(loc.latitude, 2), round(loc.longitude, 2))
            if identifier not in seen:
                seen.add(identifier)
                unique_locations.append(loc)

        return unique_locations[:max_results]

    except Exception as e:
        print(f"Geocoding error in get_closest_city_matches: {e}")
        return []


def distance_between_places(point: str, target: str) -> float:
    """Calculates the distance between two places."""
    geolocator = Nominatim(user_agent=USER_AGENT, timeout=TIMEOUT)
    try:
        start = geolocator.geocode(point, addressdetails=True, language=DEFAULT_LANGUAGE)
        end = geolocator.geocode(target, addressdetails=True, language=DEFAULT_LANGUAGE)

        if start and end:
            return distance((start.latitude, start.longitude), (end.latitude, end.longitude)).km
        else:
            return float('inf')  # One or both places not found
    except Exception as e:
        print(f"Geocoding error in distance_between_places: {e}")
        return float('inf')


def what_is_there(point: Union[str, Tuple[float, float]]) -> Optional[Location]: #Changed return type to object
    """Reverse geocodes a point and returns the most relevant place."""
    geolocator = Nominatim(user_agent=USER_AGENT, timeout=TIMEOUT)
    try:
        locations = geolocator.reverse(
            point,
            addressdetails=True,
            language=DEFAULT_LANGUAGE,
            exactly_one=False
        )

        if not locations:
            return None

        places = sorted(
            locations,
            key=lambda loc: (
                bool(loc.raw['address'].get('city') or loc.raw['address'].get('state')),
                loc.raw.get('importance', 0)
            ),
            reverse=True
        )

        return places[0]
    except Exception as e:
        print(f"Geocoding error in what_is_there: {e}")
        return None

