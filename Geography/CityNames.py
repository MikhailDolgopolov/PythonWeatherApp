from geopy import Location
def get_readable_names(cities:list[Location]):
    return [get_readable_name(c) for c in cities]

def get_readable_name(city:Location):
    address = city.raw["address"]
    name = address.get('city') or address.get('town') or address.get('village') or address.get('neighbourhood') or address.get('suburb')
    state = address.get('state') or address.get('region') or address.get('county') or address.get('state_district')
    try:
        state = address.get('region') or address.get('state_district') or address.get('county') if name in state else state
    except:
        pass
    state = address.get('region') or address.get('state_district') or address.get('county') if name in state else state

    result = f"{name}, {state}" if state else name
    return result