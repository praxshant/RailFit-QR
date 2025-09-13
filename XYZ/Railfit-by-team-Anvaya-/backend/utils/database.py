import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///railway_qr.db')
_engine = create_engine(DATABASE_URL, echo=False, future=True)
_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

# Lazy import models to avoid circular deps

def init_db():
    try:
        from backend.models.railway_item import Base as Base2
    except Exception:
        from models.railway_item import Base as Base2
    # Create all tables
    Base2.metadata.create_all(bind=_engine)


def get_db_session():
    return _SessionLocal()
