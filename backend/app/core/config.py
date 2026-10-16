from functools import lru_cache
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment or defaults."""

    # API Keys
    GROQ_API_KEY: str = Field(default="", description="API key for Groq Cloud")

    # Models
    GROQ_MODEL: str = Field(default="openai/gpt-oss-20b", description="Groq LLM model name")
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace sentence-transformers model",
    )

    # Server Configuration
    API_HOST: str = Field(default="127.0.0.1", description="FastAPI host")
    API_PORT: int = Field(default=8000, description="FastAPI port")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: Union[List[str], str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
            "*",
        ],
        description="Allowed CORS origins or comma-separated string",
    )

    # Storage and Caching
    FAISS_STORAGE_DIR: str = Field(
        default=str(Path(__file__).resolve().parent.parent / "storage"),
        description="Directory for persisting FAISS vector indexes",
    )
    CACHE_TTL_HOURS: int = Field(default=24, description="Cache expiration in hours")

    # Constraints and Retrieval
    MAX_QUESTION_LENGTH: int = Field(default=1000, description="Maximum character length for queries")
    RETRIEVAL_K: int = Field(default=4, description="Number of documents to retrieve")
    RETRIEVAL_FETCH_K: int = Field(default=20, description="Number of candidate documents for MMR")
    RETRIEVAL_LAMBDA_MULT: float = Field(default=0.5, description="MMR diversity weighting parameter")

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()

