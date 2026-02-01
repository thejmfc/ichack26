from sqlmodel import SQLModel, Field

class Property(SQLModel):
    id: int = Field(default=None, primary_key=True)
    price_per_person: float | None 
    city: str
    bedrooms: int
    bathrooms: int
    distance: float
    bills_included: bool
    amenities: list[str]
    description: str
 
class UserPreference(SQLModel):
    price: float | None
    bedrooms: int | None
    bathrooms: int | None
    distance: float | None
    bills_included: bool | None
    amenities: list[str] | None