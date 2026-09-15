from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    typesense_host: str = "localhost"
    typesense_port: int = 8108
    typesense_protocol: str = "http"
    typesense_api_key: str = "xyz"
    typesense_collection: str = "documents"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def typesense_url(self) -> str:
        return f"{self.typesense_protocol}://{self.typesense_host}:{self.typesense_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
