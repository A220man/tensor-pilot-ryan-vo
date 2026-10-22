from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "tensor-pilot-ryan-vo"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./data/tensor_pilot.db"
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # LLM settings (optional, non-secret)
    llm_provider: str = "openai-compatible"
    llm_model: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""

    # OIDC/Keycloak settings
    oidc_issuer_url: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()