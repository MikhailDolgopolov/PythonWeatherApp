from pprint import pprint

from geopy import Location


class WeatherPlace:
    def __init__(self, loc:Location):
        self.location = loc
        self.raw = loc.raw
        self.address = self.raw['address']
        self.type = self.raw['type']

        #{'region', 'state', 'country', 'city', 'suburb', 'town', 'village', 'hamlet'}

        g1 = ['hamlet', 'village', 'suburb', 'neighborhood']
        g2 = ['town', 'city', 'county', 'city_district']
        g3 = ['region', 'state']
        g4 = ['country']

        self.address_list = []
        for divs in [g1, g2, g3, g4]:
            tries = [self.address.get(div, None) for div in divs]
            my_div = next((x for x in tries if x is not None and 'округ' not in x), None)
            if my_div:
                self.address_list.append(my_div)

        pprint(self.address_list)
        print(loc.latitude, loc.longitude)



    def __str__(self):
        return str(self.location)

    def __repr__(self):
        return str(self.location)

    @property
    def latitude(self):
        return self.location.latitude
    @property
    def longitude(self):
        return self.location.longitude
