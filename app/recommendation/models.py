from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class Property(SQLModel):
    id: int = Field(default=None, primary_key=True)
    price_per_person: float | None 
    city: str
    bedrooms: int
    bathrooms: int
    distance: float
    vibe: str
    bills_included: bool
    amenities: list[str]
    description: str
 
class UserPreference(BaseModel):
    max_price: float | None
    city: str | None
    min_bedrooms: int | None
    min_bathrooms: int | None
    max_distance: float | None
    vibe: str | None
    prefer_bills_included: bool | None
    amenities: list[str] | None