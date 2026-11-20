import os
from typing import Optional

class Settings:
    PROJECT_NAME: str = "PharmIntel"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("PHARMINTEL_SECRET_KEY", "pharmintel-super-secure-production-ready-jwt-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # LLM Settings (PROVIDER-INDEPENDENT, NO GEMINI FLASH!)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local_engine")  # local_engine | ollama | openai | gemini_pro
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", None)
    LLM_BASE_URL: Optional[str] = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "med-llama3-8b")  # Or gpt-4o, gemini-1.5-pro (NEVER FLASH)

    # Upload directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    PRESCRIPTION_DIR: str = os.path.join(BASE_DIR, "uploads", "prescriptions")
    ML_MODELS_DIR: str = os.path.join(BASE_DIR, "ml", "saved_models")
    ML_RESULTS_DIR: str = os.path.join(BASE_DIR, "ml", "results")

    # Canonical Database Path
    DB_PATH: str = os.path.join(BASE_DIR, "pharmintel.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.replace(os.sep, '/')}")

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PRESCRIPTION_DIR, exist_ok=True)
os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)
os.makedirs(settings.ML_RESULTS_DIR, exist_ok=True)
