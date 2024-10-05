from geopy import Location

from Geography.CityNames import get_readable_name
from Geography.Geography import get_closest_city_matches, city_types, what_is_there


class Place:
    def __init__(self, city_name:str):
        self.location:Location = get_closest_city_matches(city_name)[0]
        self.display_name = get_readable_name(self.location)

        self.city_coords = self.location.latitude, self.location.longitude

    def set_new_point(self, coords):
        new_loc = what_is_there(coords)
        self.set_new_location(new_loc)

    def set_new_location(self, new_loc:Location|str):
        if isinstance(new_loc, str):
            new_loc = get_closest_city_matches(new_loc)[0]
        self.display_name = get_readable_name(new_loc)
        if new_loc.type in city_types:
            self.location = new_loc
            self.city_coords = new_loc.latitude, new_loc.longitude

    def __str__(self):
        return self.display_name
