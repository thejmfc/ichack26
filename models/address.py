import requests
import urllib.parse

from geopy.distance import geodesic
from sqlmodel import SQLModel


POSTCODES_IO_API_BASE_URL = "https://api.postcodes.io/postcodes"

class Address(SQLModel):
    address_line_1: str
    address_line_2: str
    postcode: str

    def get_postcode_data(self) -> dict:
        url = f"{POSTCODES_IO_API_BASE_URL}/{urllib.parse.quote(self.postcode)}"
        return requests.get(url).json()

    def distance_from(self, other: "Address") -> int:
        """Calculates the geodesic distance between two locations in kilometers.

        Under the hood, this uses the latitude and longitude of each location's postcode.
        """

        return geodesic((self.latitude, self.longitude), (other.latitude, other.longitude)).km

    @property
    def latitude(self) -> float:
        data = self.get_postcode_data()
        return data["result"]["latitude"]

    @property
    def longitude(self) -> float:
        data = self.get_postcode_data()
        return data["result"]["longitude"]