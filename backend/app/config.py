from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "NeoROSHNI"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/neoroshni"
    environment: str = "development"
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
