import json
import os
from . import collection as col

collection = col.Collection()

def generate_embeddings():
    """Generate embeddings locally (original functionality)"""
    print("🔄 Generating embeddings...")
    
    # Load properties data
    properties_path = os.path.join(os.path.dirname(__file__), "../recommendation/housing_data/mock_properties.json")
    with open(properties_path) as f:
        data = json.load(f)


    embeddings = {}

    for i, property_data in enumerate(data):
        # Create property text
        text = f"""
        Address: {property_data.get('address', "")}
        Description: {property_data.get("description", "")}
        City: {property_data.get("city", "")}
        Price per person: £{property_data.get("price_per_person", "")}
        Bedrooms: {property_data.get("bedrooms", "")}
        Bathrooms: {property_data.get("bathrooms", "")}
        Distance: {property_data.get("distance", "")} km
        Bills included: {property_data.get("bills_included", "")}
        Amenities: {", ".join(property_data.get("amenities", []))}
        """
        
        # Generate embedding
        collection.insert(i, text)
