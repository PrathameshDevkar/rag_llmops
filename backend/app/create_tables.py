from backend.app.core.database import engine
from backend.app.models.base import Base

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("Tables created")
