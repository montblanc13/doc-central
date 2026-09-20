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
    google_drive_credentials_file: str = "secrets/google-drive/credentials.json"
    google_drive_token_file: str = "data/google-drive-token.json"
    google_drive_folder_id: str | None = None
    google_drive_source_name: str = "google-drive"
    google_drive_page_size: int = 100
    ai_provider: str = "openai"
    openai_model: str = "gpt-5-mini"
    anthropic_model: str = "claude-sonnet-4-6"
    ai_max_input_chars: int = 20000
    ai_max_output_tokens: int = 180
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def typesense_url(self) -> str:
        return f"{self.typesense_protocol}://{self.typesense_host}:{self.typesense_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
