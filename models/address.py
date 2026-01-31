from sqlmodel import SQLModel


class Address(SQLModel):
    address_line_1: str
    address_line_2: str
    postcode: str