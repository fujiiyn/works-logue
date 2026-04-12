from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:54322/postgres"
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_service_role_key: str = ""

    # Google Cloud / Vertex AI
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    google_application_credentials: str = ""

    # App
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": (".env", ".env.local"), "env_file_encoding": "utf-8"}


settings = Settings()
