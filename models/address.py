import requests
import urllib.parse

from geopy.distance import geodesic
from sqlmodel import SQLModel


POSTCODES_IO_API_BASE_URL = "https://api.postcodes.io/postcodes"

class Address(SQLModel):
    address_line_1: str
    address_line_2: str
    city: str
    postcode: str
    latitude: float
    longitude: float

    @staticmethod
    def get_coordinates(postcode: str) -> tuple:
        url = f"{POSTCODES_IO_API_BASE_URL}/{urllib.parse.quote(postcode)}"
        res = requests.get(url).json()
        return res["result"]["latitude"], res["result"]["longitude"]

    @staticmethod
    def distance(a: "Address", b: "Address") -> int:
        """Calculates the geodesic distance between two locations in kilometers."""

        return geodesic((a.latitude, a.longitude), (b.latitude, b.longitude)).km

    @classmethod
    def new(cls, postcode: str, **kwargs) -> "Address":
        latitude, longitude = cls.get_coordinates(postcode)
        return cls(
            **kwargs,
            postcode=postcode,
            latitude=latitude,
            longitude=longitude)