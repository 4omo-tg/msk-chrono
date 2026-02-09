from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Moscow Chrono Walker"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = []
    
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = "moscow_chrono_bot"
    
    # AI API Settings (Qwen AI Proxy)
    AI_API_BASE_URL: str = "https://ai-proxxy.exe.xyz/api"
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "qwen3-vl-plus"  # Latest Qwen3 VL model
    
    # GeminiGen.AI API (Time Machine image generation)
    GEMINIGEN_API_KEY: str = ""
    
    # Site URL (for Telegram bot links)
    SITE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

settings = Settings()
