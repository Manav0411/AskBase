from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Global variables - lazy initialized
engine = None
SessionLocal = None
Base = declarative_base()
_db_initialized = False

def get_engine():
    """Lazy initialization of database engine"""
    global engine
    if engine is None:
        # Add connection pool settings to prevent hanging
        engine_args = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": {}
        }

        if settings.database_url.startswith("sqlite"):
            engine_args["connect_args"]["check_same_thread"] = False
        elif settings.database_url.startswith("postgresql"):
            engine_args["connect_args"]["connect_timeout"] = 10

        engine = create_engine(settings.database_url, **engine_args)
    return engine

def get_session_local():
    """Lazy initialization of session factory"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal

def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    Initializes database tables on first use.
    """
    global _db_initialized
    if not _db_initialized:
        try:
            Base.metadata.create_all(bind=get_engine())
            _db_initialized = True
        except Exception as e:
            print(f"Database initialization failed: {e}")
            # Continue anyway - will retry on next request
            
    session_factory = get_session_local()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    global _db_initialized
    Base.metadata.create_all(bind=get_engine())
    _db_initialized = True
