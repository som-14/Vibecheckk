# Plain-English description: Configures the SQLAlchemy database engine, session factory, and request-level dependency.

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import DATABASE_URL

# Connect arguments (e.g. check_same_thread for SQLite test environments)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    # Database session generator providing clean teardown per request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

