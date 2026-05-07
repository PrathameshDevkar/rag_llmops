from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
import psycopg

conn = psycopg(
    db_name = "",
    user = "",
    password = ""
)
cur = conn.cursor()

cur.execute("SELECT * FROM users WHERE username = %s, ("abc",))

row = cur.fetchall()


"""
