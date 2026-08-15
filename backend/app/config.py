from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "NeoROSHNI"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/neoroshni"
    environment: str = "development"
    frontend_origin: str = "http://localhost:5173"
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14


settings = Settings()
