import os
from colorama import Fore
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Project Metadata
    PROJECT_NAME: str = "Langgraph RAG BACKEND"
    
    # Database Configuration
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # JWT / Security Configuration
    SECRET_KEY: str = "dev-secret-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    HUGGINGFACE_API_KEY: str
    
    # Auto-load configuration from .env file
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE",".env"), #this will help the conftest to force the settings to use the ENV_FILE = .env.test instead of .env file
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Computed DB URLs
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def psycopg_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Print verification block on init
    def __init__(self, **values):
        super().__init__(**values)
        print(Fore.YELLOW + f"=============database name is: {self.DB_NAME}=================" + Fore.RESET)


# Clean export for the rest of your app
settings = Settings()