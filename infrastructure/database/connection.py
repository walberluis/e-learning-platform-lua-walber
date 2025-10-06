"""
Database connection and configuration module.
Infrastructure Layer - Database Package
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import platform
from dotenv import load_dotenv

load_dotenv()

# Determine default database URL based on platform
def get_default_database_url():
    """Get default database URL based on platform and availability."""
    # Check if PostgreSQL URL is provided
    pg_url = os.getenv("POSTGRES_URL")
    if pg_url:
        return pg_url
    
    # For Windows or development, use SQLite as default
    if platform.system() == "Windows" or os.getenv("USE_SQLITE", "false").lower() == "true":
        db_path = os.path.join(os.getcwd(), "elearning.db")
        return f"sqlite:///{db_path}"
    
    # Default PostgreSQL URL for production
    return "postgresql://elearning_user:elearning_pass@localhost:5432/elearning_db"

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", get_default_database_url())

# Create SQLAlchemy engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False  # Disable SQLAlchemy logging by default
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=False  # Disable SQLAlchemy logging by default
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_database():
    """
    Dependency to get database session.
    Yields database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    try:
        # Import models to register them with Base
        import infrastructure.database.models  # This will register all models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # Try to provide more helpful error information
        if "TypingOnly" in str(e):
            print("This appears to be a SQLAlchemy version compatibility issue.")
            print("   Try upgrading SQLAlchemy: pip install --upgrade sqlalchemy")
        raise e

def close_database():
    """
    Close database connections.
    """
    engine.dispose()
    print("Database connections closed.")
