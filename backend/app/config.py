"""Application configuration via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/signal.db"

    # Security
    secret_key: str = "change-me-to-a-random-secret-key-at-least-32-chars"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Environment
    environment: str = "development"

    # Session
    session_expiry_days: int = 7

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def database_path(self) -> Path:
        """Extract the file path from the database URL."""
        # sqlite+aiosqlite:///./data/signal.db → ./data/signal.db
        path_str = self.database_url.split("///")[-1]
        return Path(path_str)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
