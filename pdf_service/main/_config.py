import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    ENVIRONMENT: str = "local"
    LOGGING_LEVEL: int = logging.INFO

    SQLALCHEMY_DATABASE_URI: str
    RABBITMQ_CONNECTION: str
    SQLALCHEMY_ENGINE_OPTIONS: dict = {}
    SQLALCHEMY_ECHO: bool = False

    # RabbitMQ settings
    RABBITMQ_CONNECTION: str
    RABBITMQ_QUEUE_TRANSLATE_TO_PDF: str

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding="utf-8",
    )

    # Redis settings
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0


environment = os.environ.get("ENVIRONMENT", "local")
config = Config(
    ENVIRONMENT=environment,
    # ".env.{environment}" takes priority over ".env"
    _env_file=[".env", f".env.{environment}"],
)
