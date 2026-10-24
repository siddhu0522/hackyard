from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# SQLite connection with connect_args for multithreading in FastAPI
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models to ensure they are registered with Base metadata
    import backend.app.models.repository
    import backend.app.models.specification
    import backend.app.models.scan
    import backend.app.models.detected_change
    import backend.app.models.affected_file
    import backend.app.models.repair_attempt
    import backend.app.models.proposed_patch
    import backend.app.models.test_run
    import backend.app.models.pull_request
    import backend.app.models.monitoring
    
    Base.metadata.create_all(bind=engine)
