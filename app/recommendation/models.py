from sqlmodel import SQLModel, Field

class Property(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    price_per_person: float
    city: str
    bedrooms: int
    distance: float
    vibe: str
    bills_included: bool
    amenities: list[str]
    description: str

class UserPreference(SQLModel, table=True):
    max_price: float
    city: str
    min_bedrooms: int
    max_distance: float
    vibe: str
    prefer_bills_included: bool
    amenities: list[str]