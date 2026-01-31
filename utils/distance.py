import models

from geopy.distance import geodesic


def distance_between(address_1: models.Address, address_2: models.Address) -> int:
    """Calculates the geodesic distance between two locations in kilometers.

    Under the hood, this uses the latitude and longitude of each location's postcode.
    """

    return geodesic((address_1.latitude, address_1.longitude), (address_2.latitude, address_2.longitude)).km
