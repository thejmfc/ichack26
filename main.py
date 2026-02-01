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

# Database will be initialized on first use via get_engine()
print("[*] Database will be initialized on startup...")


from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json
import shutil

# Import semantic search modules

from semantic_search.collection import Collection
import threading
import time
def run_generate_embeddings():
    try:
        from semantic_search.generate_embeds import generate_embeddings
        generate_embeddings()
    except Exception as e:
        print(f"[WARNING] Error generating embeddings: {e}")




log = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # Initialize database engine once at startup
    try:
        from database import get_engine
        engine = get_engine()
        print("[OK] Database initialization completed successfully!")
        print(f"Database URL: {engine.url}")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Start embeddings generation in background
    threading.Thread(target=run_generate_embeddings, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files directory for serving images
IMAGES_DIR = Path(__file__).parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# Mount the images directory to serve files at /images/ endpoint
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

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
def get_properties(db: Session = Depends(get_db)):
    """Return the full list of properties from the database."""
    properties = db.exec(select(MockProperty)).all()
    
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
            "description": prop.description,
            "image": prop.image,
            "niceness_rating": prop.niceness_score,
        })
    
    return result


@app.get("/properties/{id}")
def get_property(id: int, db: Session = Depends(get_db)):
    """Return a single property by its ID. Returns 404 if not found."""
    property = db.get(MockProperty, id)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    try:
        amenities = json.loads(property.amenities) if property.amenities else []
    except (json.JSONDecodeError, TypeError):
        amenities = []
    
    return {
        "id": property.id,
        "price_per_person": property.price_per_person,
        "city": property.city,
        "address": property.address,
        "bedrooms": property.bedrooms,
        "bathrooms": property.bathrooms,
        "distance": property.distance,
        "vibe": property.vibe,
        "bills_included": property.bills_included,
        "amenities": amenities,
        "description": property.description,
        "image": property.image,
        "niceness_rating": property.niceness_score,
    }

@app.post("/properties/{property_id}/upload-image")
async def upload_property_image(property_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload an image for a property"""
    # Verify property exists
    property_obj = db.get(MockProperty, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    # Validate file type
    allowed_extensions = {"jpg", "jpeg", "png", "gif", "webp"}
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {allowed_extensions}")
    
    # Save file
    filename = f"property_{property_id}.{file_ext}"
    file_path = IMAGES_DIR / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update database with image URL
        image_url = f"/images/{filename}"
        property_obj.image = image_url
        db.add(property_obj)
        db.commit()
        
        return {
            "message": "Image uploaded successfully",
            "property_id": property_id,
            "image": image_url,
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@app.get("/properties/{property_id}/image")
def get_property_image(property_id: int, db: Session = Depends(get_db)):
    """Get image URL for a property"""
    property_obj = db.get(MockProperty, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if not property_obj.image:
        raise HTTPException(status_code=404, detail="No image available for this property")
    
    return {"property_id": property_id, "image": property_obj.image}

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
            "description": prop.description,
            "niceness_rating": prop.niceness_score,
        })
    
    return result


@app.post("/user/preferences/{property_id}")
def update_preferences(property_id: int, db: Session = Depends(get_db)):
    """Update user preferences based on property selection"""
    property_obj = db.exec(select(MockProperty).where(MockProperty.id == property_id)).first()
    user_pref = db.exec(select(UserPreferences).where(UserPreferences.user_id == 1)).first()

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if not user_pref:
        # Create default user preferences if they don't exist
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        user_pref = UserPreferences(
            user_id=1,
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


    print(user_pref)
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

    # Update weights to converge around a mean (moving average approach)
    # Instead of a fixed target mean, use the running average of selected properties

    learning_rate = 0.2

    # Retrieve or initialize running means for each feature
    try:
        running_means = json.loads(user_pref.__dict__.get("running_means", "{}"))
    except (json.JSONDecodeError, TypeError):
        running_means = {}

    # Count of selections for running mean calculation
    selection_count = user_pref.__dict__.get("selection_count", 0)
    if not isinstance(selection_count, int):
        try:
            selection_count = int(selection_count)
        except Exception:
            selection_count = 0
    selection_count += 1

    # Helper to update running mean
    def update_mean(old_mean, new_value, n):
        if old_mean is None:
            return new_value
        return old_mean + (new_value - old_mean) / n

    # Update running means
    features = [
        ("price", property_obj.price_per_person),
        ("bedrooms", property_obj.bedrooms),
        ("bathrooms", property_obj.bathrooms),
        ("distance", property_obj.distance),
        ("bills_included", int(property_obj.bills_included) if property_obj.bills_included is not None else None),
        ("amenities", None)
    ]
    # Calculate amenities count
    if property_obj.amenities:
        try:
            amenities = json.loads(property_obj.amenities)
            features[-1] = ("amenities", len(amenities) if amenities else 0)
        except (json.JSONDecodeError, TypeError):
            features[-1] = ("amenities", 0)
    else:
        features[-1] = ("amenities", 0)

    for key, value in features:
        if value is not None:
            old_mean = running_means.get(key)
            running_means[key] = update_mean(old_mean, value, selection_count)

    # Now update weights to move toward the running mean
    for key, value in features:
        if value is not None:
            diff = value - running_means[key]
            current_weights[key] += learning_rate * diff

    # Store updated running means and selection count in user_pref (as JSON/text fields)
    user_pref.__dict__["running_means"] = json.dumps(running_means)
    user_pref.__dict__["selection_count"] = selection_count

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
    user_pref = db.exec(select(UserPreferences).where(UserPreferences.user_id == 1)).first()
    
    if not user_pref:
        # Return default preferences
        return {
            "user_id": 1,
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