import datetime, os, requests

from .address import Address
from sqlmodel import Field
from pydantic import computed_field
from urllib.parse import urlencode


EPC_API_BASE_URL = "https://epc.opendatacommunities.org/api/v1/domestic/search"
EPC_API_KEY = os.getenv("EPC_API_KEY")

# All data sourced from Ofgem: https://www.ofgem.gov.uk/information-consumers/energy-advice-households/energy-price-cap-explained
ELECTRICITY_PRICE_CAP = 27.69 # pence per kWh as of Jan 2026
GAS_PRICE_CAP = 5.93 # pence per kWh as of Jan 2026
ELECTRICITY_STANDING_CHARGE_CAP = 54.75 # pence per day as of Jan 2026
GAS_STANDING_CHARGE_CAP = 35.09 # pence per day as of Jan 2026
ENERGY_STANDING_CHARGES = 365 * (ELECTRICITY_STANDING_CHARGE_CAP + GAS_STANDING_CHARGE_CAP) / 100

class Property(Address, table=True):
    __tablename__ = "properties"

    id: int = Field(primary_key=True)
    bedrooms: int
    bathrooms: int
    unihomes_bills: int
    rent_weekly: float

    contract_start: datetime.datetime
    contract_end: datetime.datetime

    def get_energy_consumption_estimate(self, epc: dict) -> float:
        energy_per_m2 = int(epc["energy-consumption-current"])
        floor_area = float(epc["total-floor-area"])
        return energy_per_m2 * floor_area

    def get_energy_cost_estimate(self, consumption: float) -> float:
        return ENERGY_STANDING_CHARGES + (consumption * ELECTRICITY_PRICE_CAP / 100)

    def get_epc(self) -> dict:
        headers = {"Accept": "application/json", "Authorization": f"Basic {EPC_API_KEY}"}
        search_params = urlencode({"address": self.address_line_1, "postcode": self.postcode, "size": 1})
        res = requests.get(f"{EPC_API_BASE_URL}?{search_params}", headers=headers)
        return res.json()["rows"][0]

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
