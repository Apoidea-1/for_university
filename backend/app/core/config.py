from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "NetWorkPilot API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "<CHANGE_ME>"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/networkpilot"
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173"
    )
    demo_user_email: str = "demo@networkpilot.app"
    demo_user_password: str = "DemoPass123!"
    demo_user_name: str = "Alex Morgan"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.cors_origins
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
