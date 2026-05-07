# settings.py
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\.env" ,override=True)

class Settings:
    PROJECT_NAME = "Langgraph RAG BACKEND"

    def __init__(self):
        self.DB_HOST = os.getenv("DB_HOST")
        self.DB_PORT = os.getenv("DB_PORT")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")

        print("==========================================")
        print("database name is", self.DB_NAME)

        self.DATABASE_URL = (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

        self.psycopg_URL = (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
ALGORITHM = os.getenv("JWT_ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRE_MINUTES",60)
