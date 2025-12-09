"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database path - use /app/data for Docker volume mount
DATA_DIR = os.environ.get("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR}/health_monitor.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from app.models import Admin, Settings, MonitoredModel, TestResult, DebugLog
    from sqlalchemy import inspect, text
    from app.logger import log_debug
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Apply migrations for existing databases
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        # Check monitored_models table
        columns = [col['name'] for col in inspector.get_columns('monitored_models')]
        if 'sort_order' not in columns:
            db.execute(text("ALTER TABLE monitored_models ADD COLUMN sort_order INTEGER DEFAULT 0"))
            db.commit()
            log_debug("INFO", "database", "Added sort_order column to monitored_models")
        
        # Check settings table
        settings_columns = [col['name'] for col in inspector.get_columns('settings')]
        
        if 'test_start_hour' not in settings_columns:
            db.execute(text("ALTER TABLE settings ADD COLUMN test_start_hour INTEGER DEFAULT 0"))
            db.commit()
            log_debug("INFO", "database", "Added test_start_hour column to settings")
        
        if 'test_start_minute' not in settings_columns:
            db.execute(text("ALTER TABLE settings ADD COLUMN test_start_minute INTEGER DEFAULT 0"))
            db.commit()
            log_debug("INFO", "database", "Added test_start_minute column to settings")
        
        if 'custom_notification_text' not in settings_columns:
            db.execute(text("ALTER TABLE settings ADD COLUMN custom_notification_text TEXT DEFAULT ''"))
            db.commit()
            log_debug("INFO", "database", "Added custom_notification_text column to settings")
            
    except Exception as e:
        log_debug("ERROR", "database", f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()


