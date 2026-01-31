import json
import os
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str):
    """Generate embeddings using SentenceTransformer"""
    cleaned_text = " ".join(text.split())
    embedding = model.encode(cleaned_text, convert_to_tensor=False)
    return embedding.tolist()

def generate_embeddings(text: str):
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
        embedding = embed_text(text)
        
        # Store with property ID
        property_id = property_data.get("id", i + 1)
        embeddings[str(property_id)] = embedding
        
        print(f"Generated embedding for property {property_id} in {property_data.get('city', 'Unknown')}")

    print(f"\nGenerated embeddings for {len(embeddings)} properties")

    # Save embeddings
    embeddings_path = os.path.join(os.path.dirname(__file__), "../recommendation/housing_data/mock_embeddings.json")
    with open(embeddings_path, "w") as f:
        json.dump(embeddings, f, indent=2)
    
    print(f"✅ Embeddings saved to {embeddings_path}")
