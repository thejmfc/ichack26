from models import Property, UserPreference
from data_loading import load_mock_properties, load_mock_user_preferences
from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import os
from sqlalchemy.orm import Session
from fastapi import Depends
from models import Property as PropertyModel
from models import UserPreference as UserPreferenceModel

app = FastAPI()

class PropertyWithScore(BaseModel):
    property: Property
    score: float

class RecommendationRequest(BaseModel):
    user_preferences: UserPreference
    limit: Optional[int] = 10

def score_property(property: Property, user_preferences: UserPreference):
    score = 0
    
    # Price scoring - higher score for properties within budget
    if user_preferences.price and property.price_per_person:
        if property.price_per_person <= user_preferences.price:
            # Bonus points for being under budget, more points for being further under
            score += (user_preferences.price - property.price_per_person) / 10
        else:
            # Penalty for being over budget
            score -= (property.price_per_person - user_preferences.price) / 5

    # Bedroom requirements - bonus for meeting or exceeding minimum
    if user_preferences.bedrooms and property.bedrooms:
        if property.bedrooms >= user_preferences.bedrooms:
            score += 10 + (property.bedrooms - user_preferences.bedrooms)
        else:
            # Penalty for not meeting minimum
            score -= (user_preferences.bedrooms - property.bedrooms) * 5

    # Bathroom requirements - bonus for meeting or exceeding minimum
    if user_preferences.bathrooms and property.bathrooms:
        if property.bathrooms >= user_preferences.bathrooms:
            score += 8 + (property.bathrooms - user_preferences.bathrooms)
        else:
            # Penalty for not meeting minimum
            score -= (user_preferences.bathrooms - property.bathrooms) * 3

    # Distance scoring - bonus for being within max distance, more points for closer
    if user_preferences.distance and property.distance:
        if property.distance <= user_preferences.distance:
            score += (user_preferences.distance - property.distance) / 2
        else:
            # Penalty for being too far
            score -= (property.distance - user_preferences.distance)
    
    # Bills included preference
    if user_preferences.bills_included is not None and property.bills_included is not None:
        if user_preferences.bills_included == property.bills_included:
            score += 8
        elif user_preferences.bills_included and not property.bills_included:
            score -= 3
    
    # Amenities matching - points for each matching amenity
    if user_preferences.amenities and property.amenities:
        matching_amenities = set(user_preferences.amenities) & set(property.amenities)
        score += len(matching_amenities) * 3
        
        # Bonus if all preferred amenities are available
        if len(matching_amenities) == len(user_preferences.amenities):
            score += 5
    
    return score


# Helper function to load properties
def get_all_properties() -> list[Property]:
    try:
        # Adjust path relative to the current working directory
        file_path = os.path.join(os.path.dirname(__file__), '../housing_data/mock_properties.json')
        return load_mock_properties(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load properties: {str(e)}")

def get_user_preferences() -> UserPreference:
    try:
        file_path = os.path.join(os.path.dirname(__file__), '../housing_data/user_preferences.json')
        return load_mock_user_preferences(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load user preferences: {str(e)}")

def recommend_properties(properties: list[Property], user_preferences: UserPreference, limit: int = 10):
    scored_properties = [
        (property, score_property(property, user_preferences))
        for property in properties
    ]
    scored_properties.sort(key=lambda x: x[1], reverse=True)
    top = scored_properties[:limit]
    return [property for property, score in top]

def recommend_properties_with_scores(properties: list[Property], user_preferences: UserPreference, limit: int = 10):
    """Return recommendations as (property, score) tuples for testing and API use"""
    scored_properties = [
        (property, score_property(property, user_preferences))
        for property in properties
    ]
    scored_properties.sort(key=lambda x: x[1], reverse=True)
    return scored_properties[:limit]

# FastAPI Endpoints
@app.get("/", summary="Health Check")
def root():
    return {"message": "Property Recommendation API is running"}


@app.get("/properties", response_model=list[Property], summary="Get All Properties")
def get_properties():
    return get_all_properties()


@app.post("/recommendations", response_model=list[PropertyWithScore], summary="Get Property Recommendations with Scores")
def get_recommendations(request: RecommendationRequest):
    properties = get_all_properties()
    
    if not properties:
        raise HTTPException(status_code=404, detail="No properties found")
    
    recommendations = recommend_properties_with_scores(
        properties, 
        request.user_preferences, 
        request.limit
    )
    
    return [
        PropertyWithScore(property=property, score=score) 
        for property, score in recommendations
    ]


@app.post("/recommendations/properties", response_model=list[Property], summary="Get Property Recommendations")
def get_property_recommendations_endpoint(request: RecommendationRequest):
    properties = get_all_properties()
    
    if not properties:
        raise HTTPException(status_code=404, detail="No properties found")

    return recommend_properties(
        properties,
        request.user_preferences,
        request.limit
    )


@app.post("/properties/{property_id}/score", response_model=float, summary="Score a Specific Property")
def score_property_endpoint(property_id: int, user_preferences: UserPreference):
    properties = get_all_properties()
    
    property_obj = next((p for p in properties if p.id == property_id), None)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return score_property(property_obj, user_preferences)


@app.get("/properties/search", response_model=list[Property], summary="Search Properties")
def search_properties(
    city: Optional[str] = Query(None, description="Filter by city"),
    max_price: Optional[float] = Query(None, description="Maximum price per person with bills"),
    min_bedrooms: Optional[int] = Query(None, description="Minimum number of bedrooms"),
    min_bathrooms: Optional[int] = Query(None, description="Minimum number of bathrooms"),
    max_distance: Optional[float] = Query(None, description="Maximum distance from city center"),
    bills_included: Optional[bool] = Query(None, description="Whether bills are included"),
):
    properties = get_all_properties()
    
    # Apply filters
    filtered_properties = properties
    
    if city:
        filtered_properties = [p for p in filtered_properties if p.city and city.lower() in p.city.lower()]
    
    if max_price is not None:
        filtered_properties = [p for p in filtered_properties if p.price_pp_bills and p.price_pp_bills <= max_price]
    
    if min_bedrooms is not None:
        filtered_properties = [p for p in filtered_properties if p.bedrooms and p.bedrooms >= min_bedrooms]
    
    if min_bathrooms is not None:
        filtered_properties = [p for p in filtered_properties if p.bathrooms and p.bathrooms >= min_bathrooms]
    
    if max_distance is not None:
        filtered_properties = [p for p in filtered_properties if p.distance and p.distance <= max_distance]
    
    if bills_included is not None:
        filtered_properties = [p for p in filtered_properties if p.bills_included == bills_included]
    
    return filtered_properties

from database import get_db  # Assumes you have a get_db dependency for DB sessions

@app.post("/user/preferences/{property_id}")
def update_preferences(property_id: int, db: Session = Depends(get_db)):
    property_obj = db.query(PropertyModel).filter(PropertyModel.id == property_id).first()
    user_pref = db.query(UserPreferenceModel).filter(UserPreferenceModel.id == 1).first()

    if not property_obj or not user_pref:
        raise HTTPException(status_code=404, detail="Property or UserPreference not found")

    # Update price preference (move max_price toward property price)
    if hasattr(user_pref, "price") and hasattr(property_obj, "price_per_person"):
        if property_obj.price_per_person is not None:
            # Move max_price 25% toward the selected property's price
            user_pref.price = (
                user_pref.price * 0.75 + property_obj.price_per_person * 0.25
                if user_pref.price is not None else property_obj.price_per_person
            )

    # Update min_bedrooms
    if hasattr(user_pref, "bedrooms") and hasattr(property_obj, "bedrooms"):
        if property_obj.bedrooms is not None:
            user_pref.bedrooms = max(
                user_pref.bedrooms or 0,
                property_obj.bedrooms
            )

    # Update min_bathrooms
    if hasattr(user_pref, "bathrooms") and hasattr(property_obj, "bathrooms"):
        if property_obj.bathrooms is not None:
            user_pref.bathrooms = max(
                user_pref.bathrooms or 0,
                property_obj.bathrooms
            )

    # Update max_distance (move toward property distance)
    if hasattr(user_pref, "distance") and hasattr(property_obj, "distance"):
        if property_obj.distance is not None:
            user_pref.distance = (
                user_pref.distance * 0.75 + property_obj.distance * 0.25
                if user_pref.distance is not None else property_obj.distance
            )

    # Update prefer_bills_included
    if hasattr(user_pref, "bills_included") and hasattr(property_obj, "bills_included"):
        if property_obj.bills_included is not None:
            user_pref.bills_included = property_obj.bills_included

    # Update amenities: add any new amenities from the property to user preferences
    if hasattr(user_pref, "amenities") and hasattr(property_obj, "amenities"):
        if property_obj.amenities:
            current_amenities = set(user_pref.amenities or [])
            property_amenities = set(property_obj.amenities)
            # Add any amenities from the property that aren't already in preferences
            user_pref.amenities = list(current_amenities | property_amenities)

    db.commit()
    db.refresh(user_pref)
    return {"message": "User preferences updated", "user_preferences": user_pref}