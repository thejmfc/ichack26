from .address import Address
from sqlmodel import Field


class Landmark(Address, table=True):
    id: int = Field(primary_key=True)
    name: str