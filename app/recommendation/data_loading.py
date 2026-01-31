import json
from models import Property
from sqlmodel import SQLModel, select

file_path = 'housing_data/mock_properties.json'

def load_mock_properties(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return [Property(**item) for item in data]

def load_from_db(session):
    return session.exec(select(Property)).all()