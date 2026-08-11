from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: int
    DB_NAME: str

    REDIS_HOST: str
    REDIS_PORT: int

    JWT_SECRET: str = "test-secret-do-not-use-elsewhere"
    JWT_EXPIRATION_IN_MINUTES: int = 15
    JWT_ALGORITHM: str = "HS256"

    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    ENV: Literal["development", "staging", "production"] = "development"

    @property
    def DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache
def get_settings():
    return Settings() # pyright: ignore[reportCallIssue]
