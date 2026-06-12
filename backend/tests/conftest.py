"""
This file builds your isolated test pipeline. It manages a clean transaction lifecycle per test, hooks into FastAPI's dependency_overrides framework to mock production databases, and 
exposes core fixtures (client, test_user, auth_token).
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Force Pydantic Settings to load the test environment file before importing the app
os.environ["ENV_FILE"] = ".env.test"

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.core.security import hash_password
from backend.app.core.auth import create_access_token

# Connect directly to your dedicated Postgres test database string
print(f"===================================={settings.SECRET_KEY}&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
TEST_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres123"
    "@localhost:5432/langgraph_rag_test"
)

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def initialize_test_database_schema():
    """Initializes extensions and sets up table schemas once for the entire test session."""
    with engine.connect() as connection:
        with connection.begin():
            # Ensure pgvector extension is explicitly active on the test database instance
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    # Build your complete production SQLAlchemy ORM schema safely
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all structures cleanly at the conclusion of the test pipeline execution loop
    Base.metadata.drop_all(bind=engine)
    
        
@pytest.fixture(scope="function")
def db_session():
    """provides a transsactional database session that rolls back automatically"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind = connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    
@pytest.fixture(scope= "function")
def client(db_session):
    """overrides app database dependency and exposes FastAPI testclient"""
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
        
    app.dependency_overrides[get_db]=_get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    
    
@pytest.fixture(scope = "function")
def test_user(db_session):
    """generate a dummy user record inside the test dataabse"""
    user = User(
        username = "test_user",
        password_hash = hash_password("test_user123")
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope = "function")
def auth_token(test_user):
    """generate a valid access token linked to the summy test user"""
    return create_access_token(subject = str(test_user.id))