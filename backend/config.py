import os

class Settings:
    PROJECT_NAME: str = "12C - AI-Based Clinical Decision Support System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database URL: default SQLite file in project directory
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'medical_travel.db')}"
    )
    
    # AI API Keys & LLM Runtime
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.38"))
    
    # JWT Auth - Strong, entropy-backed secret key with environment override
    SECRET_KEY: str = os.getenv("SECRET_KEY", "12c_sec_k9#wX!8qL2$vP0@eR7^yB4*mN1&jH5_auth_production_secret_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

settings = Settings()

