from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Squash League"
    app_env: str = "development"
    database_url: str = "sqlite:///./squash.db"
    secret_key: str = "development-only-change-me"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
