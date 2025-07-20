from os import path
from functools import lru_cache

from pydantic import PostgresDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_dsn: PostgresDsn

    model_config = SettingsConfigDict(
        env_prefix="DEPENDENCY_APP_",
        case_sensitive=False,
        env_file=path.join(path.dirname(path.abspath(__file__)), "..", "..", ".env"),
    )
