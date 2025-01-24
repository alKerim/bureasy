# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# For a local "test.db" in your project directory.
# Adjust the path or use a different DB if you want.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# 'connect_args={"check_same_thread": False}' is needed for SQLite in a single-thread environment
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session in your route
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
