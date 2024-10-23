from geopy import Location

from Geography.CityNames import get_readable_name
from Geography.Geography import get_closest_city_matches, city_types, what_is_there, get_location


class Place:
    def __init__(self, city_name:str):
        self.location:Location = get_closest_city_matches(city_name)[0]
        self.display_name = get_readable_name(self.location)

        self.coords = self.location.latitude, self.location.longitude

    def set_new_point(self, coords:tuple[float]):
        new_loc = what_is_there(coords)
        self.set_new_location(new_loc)
        self.coords = coords
    def set_new_location(self, address:str):
        new_loc = get_location(address)
        self.display_name = get_readable_name(new_loc)
        if new_loc.raw['type'] in city_types:
            self.location = new_loc


    def __str__(self):
        return self.display_name

    def full_str(self):
        return f"{self.display_name}, {', '.join([str(round(cc, 3)) for cc in self.coords])}"