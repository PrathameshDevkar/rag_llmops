import os
from colorama import Fore
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
import sys
from dotenv import load_dotenv


"""🔍 The Root Cause: Environment Variable Precedence
Look closely at your pytest plugin list from the terminal:

Plaintext
plugins: anyio-4.12.1, deepeval-4.0.6, Faker-40.15.0, langsmith-0.6.1, ...
Third-party LLM observability and evaluation plugins (specifically langsmith and deepeval) register hooks that boot up extremely early in the Pytest lifecycle—well before your test discovery loop finishes. As part of their internal startup routines, these plugins automatically search for a .env file in your project root and invoke dotenv.load_dotenv().

This means that by the time Python enters your config.py file, your system's os.environ dictionary has already been fully populated with the development/production values from your standard .env file.

According to Pydantic’s official design specs, system environment variables (os.environ) always take absolute precedence over values specified inside an env_file. Even though your env_file property successfully pointed to .env.test, Pydantic looked at os.environ, saw that keys like DB_NAME were already defined, and explicitly ignored the values inside .env.test.

🛠️ The Production Fix: Forceful Environment Overriding
To protect your configuration layer from early third-party plugin state pollution, you must explicitly force your targeted environment file back into os.environ using override=True right before Pydantic initializes the Settings class fields.
"""
# 1. Calculate the project root directory path dynamically relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 2. Hardened Environment Auto-Detection (Immune to Python Import Caching traps)
is_test_session = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)

if is_test_session:
    print(Fore.YELLOW + "\n[SYSTEM] Pytest session detected. Forcing test environment configuration." + Fore.RESET)
    target_env_file = ".env.test"
else:
    target_env_file = os.getenv("ENV_FILE", ".env")

resolved_env_path = PROJECT_ROOT / target_env_file
print(Fore.YELLOW + f"[SYSTEM] Target env file resolved to:" + Fore.RESET, resolved_env_path)

# 🔥 CRITICAL STEP: Clear early plugin contamination by forcing .env.test into os.environ
if is_test_session:
    load_dotenv(dotenv_path=resolved_env_path, override=True)


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
    # GEMINI_API_KEY: str
    
    LANGSMITH_TRACING: bool = Field(default=False)
    LANGSMITH_API_KEY: str 
    LANGSMITH_PROJECT: str = Field(default="rag_llmops_self")
    LANGSMITH_ENDPOINT: str
    
    # Auto-load configuration from .env file
    model_config = SettingsConfigDict(
        env_file=resolved_env_path, #this will help the conftest to force the settings to use the ENV_FILE = .env.test instead of .env file
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