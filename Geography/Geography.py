from geopy import Nominatim, Location


def verify_city(name):
    geolocator = Nominatim(user_agent="city_locator")
    location: Location = geolocator.geocode(name,
                                            country_codes='RU',
                                            addressdetails=True,
                                            language='ru',
                                            featuretype='city'
                                            )
    if location:
        return location.raw["name"]
    else:
        return ""
