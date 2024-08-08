from pprint import pprint

import Levenshtein
from geopy import Nominatim, Location
from geopy.exc import GeocoderTimedOut


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

