import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration settings."""
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "AI-AdaptLearn")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_adaptlearn.db")
    
    # LangChain
    # LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
    # LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    # LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    # LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "ai-adaptlearn")
    
    # Chat Settings
    MAX_CHAT_HISTORY: int = 1000
    CHAT_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()
