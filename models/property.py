import datetime

from .address import Address
from sqlmodel import Field
from pydantic import computed_field


class Property(Address, table=True):
    __tablename__ = "properties"

    id: int = Field(primary_key=True)
    bedrooms: int
    bathrooms: int
    unihomes_bills: int
    rent_weekly: float

    contract_start: datetime.datetime
    contract_end: datetime.datetime

    @computed_field
    @property
    def contract_duration(self) -> datetime.timedelta:
        return self.contract_end - self.contract_start

    @computed_field
    @property
    def rent_annual(self) -> float:
        return self.rent_weekly * 52

    @computed_field
    @property
    def rent_monthly(self) -> float:
        return self.rent_annual / 12
