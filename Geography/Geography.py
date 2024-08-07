from geopy import Nominatim, Location


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
