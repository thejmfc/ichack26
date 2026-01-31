from models import Property

class RLHFProfile:
    def __init__(self):
        self.weights = {
            "max_price": 1.0,
            "min_bedrooms": 1.0,
            "min_bathrooms": 1.0,
            "max_distance": 1.0,
            "vibe": 1.0,
            "bills_included": 1.0,
            "amenities": 1.0
        }

    def update_preferences(self, property_id: int, liked: bool):
        property_obj = Property.query.get(property_id)
        if not property_obj:
            raise ValueError(f"Property with id {property_id} not found")

        for key in self.weights:
            if liked:
                self.weights[key] += property_obj.key * 0.5
            else:
                self.weights[key] -= property_obj.key * 0.5