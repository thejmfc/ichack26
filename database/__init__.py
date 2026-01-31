import logging, os

from models import * # Needed to register models before SQLModel.metadata.create_all is called
from sqlalchemy import Engine
from sqlmodel import create_engine, SQLModel


log = logging.getLogger(__name__)


def init() -> Engine:
    engine = create_engine("postgresql://{user}:{password}@{host}:{port}/{db}".format(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        db=os.getenv("POSTGRES_DB")), echo=True)
    SQLModel.metadata.create_all(engine)
    log.info("Database initialized")
    return engine
