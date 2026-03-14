"""Configuration management for the Python API microservice."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file if it exists
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=3000, description="Server port number")
    reload: bool = Field(
        default=False, description="Enable auto-reload for development"
    )

    # Data file configuration
    data_file_path: str = Field(
        default="data.json", description="Path to the data JSON file"
    )

    # API configuration
    api_title: str = Field(default="Python API Microservice", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_description: str = Field(
        default="A FastAPI microservice for serving JSON data",
        description="API description",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    """
    Get application settings instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


def validate_data_file_path(file_path: str) -> Path:
    """
    Validate and return a Path object for the data file.

    Args:
        file_path: Path to the data file

    Returns:
        Path: Validated Path object

    Raises:
        ValueError: If the file path is invalid or contains directory traversal
    """
    path = Path(file_path).resolve()

    # Prevent directory traversal attacks
    if ".." in str(path):
        raise ValueError(f"Invalid file path: {file_path} contains directory traversal")

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return path
