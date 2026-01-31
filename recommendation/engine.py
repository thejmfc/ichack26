from models import Property, UserPreference
from data_loading import load_mock_properties, load_mock_user_preferences
from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import os

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
    if user_preferences.max_price and property.price_per_person:
        if property.price_per_person <= user_preferences.max_price:
            # Bonus points for being under budget, more points for being further under
            score += (user_preferences.max_price - property.price_per_person) / 10
        else:
            # Penalty for being over budget
            score -= (property.price_per_person - user_preferences.max_price) / 5
    
    # Bedroom requirements - bonus for meeting or exceeding minimum
    if user_preferences.min_bedrooms and property.bedrooms:
        if property.bedrooms >= user_preferences.min_bedrooms:
            score += 10 + (property.bedrooms - user_preferences.min_bedrooms)
        else:
            # Penalty for not meeting minimum
            score -= (user_preferences.min_bedrooms - property.bedrooms) * 5
    
    # Bathroom requirements - bonus for meeting or exceeding minimum  
    if user_preferences.min_bathrooms and property.bathrooms:
        if property.bathrooms >= user_preferences.min_bathrooms:
            score += 8 + (property.bathrooms - user_preferences.min_bathrooms)
        else:
            # Penalty for not meeting minimum
            score -= (user_preferences.min_bathrooms - property.bathrooms) * 3
    
    # Distance scoring - bonus for being within max distance, more points for closer
    if user_preferences.max_distance and property.distance:
        if property.distance <= user_preferences.max_distance:
            score += (user_preferences.max_distance - property.distance) / 2
        else:
            # Penalty for being too far
            score -= (property.distance - user_preferences.max_distance)
    
    # Bills included preference
    if user_preferences.prefer_bills_included is not None and property.bills_included is not None:
        if user_preferences.prefer_bills_included == property.bills_included:
            score += 8
        elif user_preferences.prefer_bills_included and not property.bills_included:
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