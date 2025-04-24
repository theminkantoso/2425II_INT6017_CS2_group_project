import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    ENVIRONMENT: str = "local"
    LOGGING_LEVEL: int = logging.INFO

    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_ENGINE_OPTIONS: dict = {}
    SQLALCHEMY_ECHO: bool = False

    # RabbitMQ settings
    RABBITMQ_QUEUE: str
    RABBITMQ_CONNECTION: str
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding="utf-8",
    )

    # Redis settings
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # SQLALCHEMY_DATABASE_URI: str = "mysql+aiomysql://root:123456@127.0.0.1/modern_sa"
    # SQLALCHEMY_ENGINE_OPTIONS: dict = {}
    # SQLALCHEMY_ECHO: bool = False
    #
    # # RabbitMQ settings
    # RABBITMQ_QUEUE: str = "gateway_to_ocr"
    # RABBITMQ_CONNECTION: str = "amqp://guest:guest@127.0.0.1:5672/"
    # model_config = SettingsConfigDict(
    #     case_sensitive=True,
    #     env_file_encoding="utf-8",
    # )
    #
    # # Redis settings
    # REDIS_HOST: str = "127.0.0.1"
    # REDIS_PORT: int = 6379
    # REDIS_DB: int = 0
    #
    MYSQL_ROOT_PASSWORD_ENV: str = ""


environment = os.environ.get("ENVIRONMENT", "local")
config = Config(
    ENVIRONMENT=environment,
    # ".env.{environment}" takes priority over ".env"
    _env_file=[".env", f".env.{environment}"],
)
