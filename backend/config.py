import os

class Settings:
    PROJECT_NAME: str = "12C - AI-Based Medical Travel Decision Support System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database URL: default SQLite file in backend directory
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./medical_travel.db")
    
    # AI API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # JWT Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "12c_medical_travel_secret_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

settings = Settings()
