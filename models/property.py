import datetime

from .address import Address
from sqlmodel import Field


class Property(Address, table=True):
    id: int = Field(primary_key=True)
    bedrooms: int
    bathrooms: int
    unihomes_bills: int
    rent_weekly: float

    contract_start: datetime.datetime
    contract_end: datetime.datetime

    @property
    def rent_annual(self) -> float:
        return self.rent_weekly * 52

    @property
    def rent_monthly(self) -> float:
        return self.rent_annual / 12