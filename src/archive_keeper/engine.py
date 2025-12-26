"""Database engine configuration."""

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from archive_keeper.models import Base

class DatabaseManager:
    """Manages SQLAlchemy database connections and sessions.
    
    Handles SQLite database initialization and provides session management
    for the Archive Keeper application.
    """
    
    def __init__(self, db_path: str = "archive.db") -> None:
        """Initialize database manager.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        # Use absolute path if possible, or relative to CWD
        self.db_url = f"sqlite:///{db_path}"
        self.engine: Engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self) -> None:
        """Create tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
