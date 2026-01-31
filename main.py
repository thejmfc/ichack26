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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json

# Import semantic search modules

from semantic_search.collection import Collection
from semantic_search.generate_embeds import generate_embeddings
generate_embeddings()



log = logging.getLogger(__name__)

app = FastAPI()

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
        
        return {
            "message": "Search completed successfully", 
            "prompt": request.prompt,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search: {str(e)}")