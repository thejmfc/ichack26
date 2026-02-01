import logging, os
import json
from typing import Optional
from sqlalchemy import Engine
from sqlmodel import create_engine, SQLModel, Session, Field, select

from models import * # Needed to register models before SQLModel.metadata.create_all is called

log = logging.getLogger(__name__)


class MockProperty(SQLModel, table=True):
    """Property model that matches the mock_properties.json structure"""
    __tablename__ = "mock_properties"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    price_per_person: int
    city: str
    address: str
    bedrooms: int
    bathrooms: int
    distance: int
    vibe: str
    bills_included: bool
    amenities: str = Field(default="")  # Store as JSON string
    description: Optional[str] = None


class UserPreferences(SQLModel, table=True):
    """User preferences model to store calibration data"""
    __tablename__ = "user_preferences"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(default="default_user")  # For now, using a default user
    feature_weights: str = Field(default="{}")  # JSON string of feature importance weights
    created_at: str = Field(default="")  # ISO timestamp
    updated_at: str = Field(default="")  # ISO timestamp

def init() -> Engine:
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.getenv("SQLITE_DB_PATH", os.path.join(db_dir, "database.db"))
    if db_path == ":memory:":
        connection_string = "sqlite:///:memory:"
    else:
        if not os.path.isabs(db_path):
            db_path = os.path.join(db_dir, db_path)
        connection_string = f"sqlite:///{db_path}"

    engine = create_engine(connection_string, echo=True)
    SQLModel.metadata.create_all(engine)
    log.info(f"SQLite database initialized at: {connection_string}")
    return engine


def init_with_mock_data() -> Engine:
    """Initialize database and populate with mock properties data and user preferences"""
    engine = init()
    
    # Load mock data
    mock_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "recommendation", "housing_data", "mock_properties.json")
    
    if not os.path.exists(mock_data_path):
        log.warning(f"Mock data file not found at: {mock_data_path}")
        return engine
    
    try:
        with open(mock_data_path, 'r', encoding='utf-8') as f:
            properties_data = json.load(f)

        with Session(engine) as session:
            # Check if property data already exists
            existing_properties = len(session.exec(select(MockProperty)).all())
            if existing_properties == 0:
                # Insert mock data using SQLModel
                for prop_data in properties_data:
                    amenities_json = json.dumps(prop_data.get('amenities', []))
                    
                    mock_property = MockProperty(
                        price_per_person=prop_data['price_per_person'],
                        city=prop_data['city'],
                        address=prop_data['address'],
                        bedrooms=prop_data['bedrooms'],
                        bathrooms=prop_data['bathrooms'],
                        distance=prop_data['distance'],
                        vibe=prop_data['vibe'],
                        bills_included=prop_data['bills_included'],
                        amenities=amenities_json,
                        description=prop_data.get('description')
                    )
                    session.add(mock_property)
                
                log.info(f"✅ Successfully inserted {len(properties_data)} properties into the database")
            else:
                log.info(f"Database already contains {existing_properties} properties. Skipping property initialization.")
            
            # Initialize user preferences
            existing_preferences = session.exec(select(UserPreferences).where(UserPreferences.user_id == "default_user")).first()
            if not existing_preferences:
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                
                user_prefs = UserPreferences(
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
                session.add(user_prefs)
                log.info("✅ Successfully initialized user preferences with null values")
            else:
                log.info("User preferences already exist. Skipping preferences initialization.")
            
            session.commit()
    
    except Exception as e:
        log.error(f"Failed to load mock data or initialize preferences: {e}")
    
    return engine


# Database dependency for FastAPI
def get_db():
    """Dependency to get database session"""
    engine = init_with_mock_data()
    with Session(engine) as session:
        yield session
