from typing import Tuple

from geopy import Location

from Geography.CityNames import get_readable_name
from Geography.Geography import get_closest_city_matches, city_types, what_is_there


class Place:
    def __init__(self, city_name: str | Location):
        """Initializes a Place object with the closest city match or with a Location object."""
        if isinstance(city_name, Location):
            self.location = city_name
        else:
            self.location = get_closest_city_matches(city_name)[0] if get_closest_city_matches(city_name) else None
        if self.location:
            self.display_name = get_readable_name(self.location)
            self.coords = (self.location.latitude, self.location.longitude)
        else:
            self.display_name = city_name  # Use the input as display name if no match found
            self.coords = None

    def set_new_point(self, new_coordinates: Tuple[float, float]):  #Renamed to be more descriptive
        """Updates the Place object with a new coordinate pair."""
        place = what_is_there(new_coordinates)
        if place:
            self.location = place
            self.display_name = get_readable_name(place)
            self.coords = (place.latitude, place.longitude)

    def __str__(self):  #Added for easier debugging and printing
        return f"Place(name={self.display_name}, coords={self.coords})"

    def full_str(self):
        return f"{self.display_name}, {', '.join([str(round(cc, 3)) for cc in self.coords])}"
