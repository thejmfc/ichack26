import json
import os
from . import collection as col
from sqlmodel import Session, select
from database import init_with_mock_data, MockProperty

collection = col.Collection()

def generate_embeddings():
    """Generate embeddings from SQLite database"""
    print("🔄 Generating embeddings from database...")
    
    # Initialize database engine
    engine = init_with_mock_data()
    
    # Fetch properties from database
    with Session(engine) as session:
        properties = session.exec(select(MockProperty)).all()
        
        if not properties:
            print("⚠️  No properties found in database. Make sure to run database initialization first.")
            return
        
        print(f"📊 Found {len(properties)} properties in database")

    for property_data in properties:
        # Parse amenities from JSON string
        try:
            amenities = json.loads(property_data.amenities) if property_data.amenities else []
        except (json.JSONDecodeError, TypeError):
            amenities = []
        
        # Create property text
        text = f"""
        Address: {property_data.address}
        Description: {property_data.description or ""}
        City: {property_data.city}
        Price per person: £{property_data.price_per_person}
        Bedrooms: {property_data.bedrooms}
        Bathrooms: {property_data.bathrooms}
        Distance: {property_data.distance} km
        Bills included: {property_data.bills_included}
        Amenities: {", ".join(amenities)}
        Image: {property_data.image}
        Niceness rating: {property_data.niceness_score}

        Metadata: {property_data.bedrooms} Students
        Price Range: {"Budget" if property_data.price_per_person < 110 else "Mid-range" if property_data.price_per_person < 150 else "Premium"}
        Property Type: {"Studio" if property_data.bedrooms == 1 else "Shared House" if property_data.bedrooms > 3 else "Apartment"}
        Location: {property_data.city}, {property_data.distance}km from campus
        """
        
        # Generate embedding using property ID from database
        collection.insert(property_data.id, text)
