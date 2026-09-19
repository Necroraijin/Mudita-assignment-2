from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "MA2"
    debug: bool = False
    environment: str = "development"
    port: int = 8000

    # Database — direct connection string (used in local dev / docker-compose)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ma2"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ma2"

    # GCP Cloud SQL — when set, overrides database_url with IAM-authed connector
    gcp_project_id: str = ""
    cloud_sql_instance: str = ""  # format: project:region:instance
    cloud_sql_database: str = "ma2"
    cloud_sql_user: str = ""
    cloud_sql_password: str = ""
    use_cloud_sql_connector: bool = False

    # Google Vertex AI (Gemini)
    vertex_ai_model: str = "gemini-2.0-flash"
    vertex_ai_location: str = "us-central1"

    # Agent config
    max_review_cycles: int = 3
    max_transcript_length: int = 50000
    max_rules_length: int = 10000

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate limiting
    rate_limit_runs_create: str = "10/minute"
    rate_limit_default: str = "60/minute"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
