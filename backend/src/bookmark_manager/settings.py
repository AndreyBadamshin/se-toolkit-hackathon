from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Smart Bookmark Manager"
    debug: bool = False

    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "bookmarks"
    postgres_user: str = "bookmarks_user"
    postgres_password: str = "bookmarks_pass"

    # Auth
    jwt_secret_key: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    # LLM (qwen-code-api OpenAI-compatible endpoint)
    llm_api_base_url: str = "http://qwen-code-api:8080/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen-plus"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
