from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "STP Banking System"
    app_version: str = "1.0.0"
    
    # Database
    database_url: str = "postgresql://postgres:mysecretpassword@localhost:5431/postgres"
    
    # JWT
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: str = ""  # .env dosyasından okunacak
    openai_model: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"

settings = Settings() 