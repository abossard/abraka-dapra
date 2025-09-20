"""Centralized configuration loading via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Base settings object that reads from environment and .env files."""

    dapr_http_port: int = 3500
    dapr_grpc_port: int = 50001
    redis_url: str = "redis://localhost:6379/0"
    ollama_endpoint: str = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:8b"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


settings = Settings()
