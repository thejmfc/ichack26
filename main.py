import logging, database
import semantic_search

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json


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


def load_properties():
    try:
        with DATA_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
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
def embed_prompt(prompt: str):
    semantic_search.generate_embeddings(prompt)