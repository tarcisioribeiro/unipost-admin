"""
Application configuration settings.

This module contains all configuration settings for the UniPOST application,
following clean code principles and security best practices.
"""

from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    """
    Application settings configuration.

    This class manages all application settings using Pydantic for
    type validation and environment variable loading.
    """

    # Django API Configuration
    django_api_url: str = Field(
        default="http://localhost:8000",
        env="DJANGO_API_URL",
        description="Base URL for Django API"
    )

    django_api_token: Optional[str] = Field(
        default=None,
        env="DJANGO_API_TOKEN",
        description="JWT token for Django API authentication"
    )

    # Elasticsearch Configuration
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        env="ELASTICSEARCH_URL",
        description="Elasticsearch cluster URL"
    )

    elasticsearch_username: str = Field(
        default="elastic",
        env="ELASTICSEARCH_USERNAME",
        description="Elasticsearch username"
    )

    elasticsearch_password: Optional[str] = Field(
        default=None,
        env="ELASTICSEARCH_PASSWORD",
        description="Elasticsearch password"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL"
    )

    # Application Settings
    secret_key: str = Field(
        default="dev-secret-key",
        env="SECRET_KEY",
        description="Application secret key"
    )

    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode flag"
    )

    # Text Generation Settings
    default_model: str = Field(
        default="gpt-3.5-turbo",
        env="DEFAULT_MODEL",
        description="Default text generation model"
    )

    max_tokens: int = Field(
        default=1000,
        env="MAX_TOKENS",
        description="Maximum tokens for text generation"
    )

    temperature: float = Field(
        default=0.7,
        env="TEMPERATURE",
        description="Temperature for text generation"
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
