# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",   # DATABASE_URL
        extra="ignore",  # e.g. OPENAI_API_KEY
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Handle SQLite vs others
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # needed for SQLite + threads
        future=True,
        echo=False,
    )
else:
    engine = create_engine(
        settings.database_url,
        future=True,
        echo=False,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()
