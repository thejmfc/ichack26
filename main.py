import logging
import importlib, sys, os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    database = importlib.import_module("ichack26.database")
except Exception:
    try:
        database = importlib.import_module("database")
    except Exception:
        sys.path.insert(0, os.path.dirname(__file__))
        database = importlib.import_module("database")

from dotenv import load_dotenv
load_dotenv()

# Add the parent directory to the path so we can import from database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Import the database initialization function
from database import init_with_mock_data, get_db, MockProperty, UserPreferences
from sqlmodel import Session, select

print("🔄 Initializing SQLite database with mock properties data...")
try:
    engine = init_with_mock_data()
    print("✅ Database initialization completed successfully!")
    print(f"Database URL: {engine.url}")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json

# Import semantic search modules

from semantic_search.collection import Collection
from semantic_search.generate_embeds import generate_embeddings
import threading
import time
def run_generate_embeddings():
    try:
        generate_embeddings()
    except Exception as e:
        logging.getLogger(__name__).error(f"Error generating embeddings: {e}")




log = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    threading.Thread(target=run_generate_embeddings, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "recommendation" / "housing_data" / "mock_properties.json"

class PromptRequest(BaseModel):
    prompt: str

def load_properties():
    try:
        with DATA_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        log.error(f"Error loading properties: {e}")
        return []


@app.get("/properties")
def get_properties():
    """Return the full list of properties from the mock JSON file."""
    return load_properties()


@app.get("/properties/{id}")
def get_property(id: int):
    """Return a single property by its index in the array (0-based). Returns 404 if not found."""
    data = load_properties()
    if id < 1 or id >= len(data):
        raise HTTPException(status_code=404, detail="Property not found")
    return data[id - 1]

@app.post("/prompt")
def embed_prompt(request: PromptRequest):
    """Search for properties using semantic search."""
    try:
        # Create collection instance
        collection_instance = Collection()
        
        # Search for similar properties
        results = collection_instance.search(request.prompt)

        print(results)

        # Return the search results
        return {
            "message": "Search completed successfully", 
            "prompt": request.prompt,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search: {str(e)}")


@app.get("/properties/db")
def get_properties_from_db(db: Session = Depends(get_db)):
    """Get properties from the SQLite database"""
    properties = db.exec(select(MockProperty)).all()
    
    if not properties:
        raise HTTPException(status_code=404, detail="No properties found in database")
    
    # Convert to format expected by frontend
    result = []
    for prop in properties:
        try:
            amenities = json.loads(prop.amenities) if prop.amenities else []
        except (json.JSONDecodeError, TypeError):
            amenities = []
        
        result.append({
            "id": prop.id,
            "price_per_person": prop.price_per_person,
            "city": prop.city,
            "address": prop.address,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "distance": prop.distance,
            "vibe": prop.vibe,
            "bills_included": prop.bills_included,
            "amenities": amenities,
            "description": prop.description
        })
    
    return result


@app.post("/user/preferences/{property_id}")
def update_preferences(property_id: int, db: Session = Depends(get_db)):
    """Update user preferences based on property selection"""
    property_obj = db.exec(select(MockProperty).where(MockProperty.id == property_id)).first()
    user_pref = db.exec(select(UserPreferences).where(UserPreferences.user_id == "default_user")).first()

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if not user_pref:
        # Create default user preferences if they don't exist
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        user_pref = UserPreferences(
            user_id="default_user",
            feature_weights=json.dumps({
                "price": 0.0,
                "bedrooms": 0.0,
                "bathrooms": 0.0,
                "amenities": 0.0,
                "distance": 0.0,
                "bills_included": 0.0,
            }),
            created_at=timestamp,
            updated_at=timestamp
        )
        db.add(user_pref)
        db.commit()
        db.refresh(user_pref)

    # Parse current feature weights
    try:
        current_weights = json.loads(user_pref.feature_weights)
    except (json.JSONDecodeError, TypeError):
        current_weights = {
            "price": 0.0,
            "bedrooms": 0.0,
            "bathrooms": 0.0,
            "amenities": 0.0,
            "distance": 0.0,
            "bills_included": 0.0,
        }

    # Update weights based on property characteristics (simple incremental learning)
    learning_rate = 0.1
    
    # Increase weight for price range
    if property_obj.price_per_person:
        current_weights["price"] = min(current_weights["price"] + learning_rate, 1.0)
    
    # Increase weight for bedrooms
    if property_obj.bedrooms:
        current_weights["bedrooms"] = min(current_weights["bedrooms"] + learning_rate, 1.0)
    
    # Increase weight for bathrooms
    if property_obj.bathrooms:
        current_weights["bathrooms"] = min(current_weights["bathrooms"] + learning_rate, 1.0)
    
    # Increase weight for distance
    if property_obj.distance:
        current_weights["distance"] = min(current_weights["distance"] + learning_rate, 1.0)
    
    # Increase weight for bills included
    if property_obj.bills_included is not None:
        current_weights["bills_included"] = min(current_weights["bills_included"] + learning_rate, 1.0)
    
    # Increase weight for amenities if property has amenities
    if property_obj.amenities:
        try:
            amenities = json.loads(property_obj.amenities)
            if amenities:
                current_weights["amenities"] = min(current_weights["amenities"] + learning_rate, 1.0)
        except (json.JSONDecodeError, TypeError):
            pass

    # Update user preferences
    from datetime import datetime
    user_pref.feature_weights = json.dumps(current_weights)
    user_pref.updated_at = datetime.now().isoformat()
    
    db.commit()
    db.refresh(user_pref)
    
    return {
        "message": "User preferences updated", 
        "property_id": property_id,
        "updated_weights": current_weights
    }


@app.get("/user/preferences")
def get_user_preferences(db: Session = Depends(get_db)):
    """Get current user preference weights"""
    user_pref = db.exec(select(UserPreferences).where(UserPreferences.user_id == "default_user")).first()
    
    if not user_pref:
        # Return default preferences
        return {
            "user_id": "default_user",
            "feature_weights": {
                "price": 0.0,
                "bedrooms": 0.0,
                "bathrooms": 0.0,
                "amenities": 0.0,
                "distance": 0.0,
                "bills_included": 0.0,
            }
        }
    
    try:
        weights = json.loads(user_pref.feature_weights)
    except (json.JSONDecodeError, TypeError):
        weights = {
            "price": 0.0,
            "bedrooms": 0.0,
            "bathrooms": 0.0,
            "amenities": 0.0,
            "distance": 0.0,
            "bills_included": 0.0,
        }
    
    return {
        "user_id": user_pref.user_id,
        "feature_weights": weights,
        "created_at": user_pref.created_at,
        "updated_at": user_pref.updated_at
    }