from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Face Attendance System"
    environment: str = "local"
    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGO_URI")
    mongo_db: str = Field(default="face_attendance", alias="MONGO_DB")
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="change-this-admin-password", alias="ADMIN_PASSWORD")
    admin_name: str = Field(default="System Admin", alias="ADMIN_NAME")
    embedding_encryption_key: str = Field(default="", alias="EMBEDDING_ENCRYPTION_KEY")
    recognition_threshold: float = Field(default=0.60, alias="RECOGNITION_THRESHOLD")
    recognition_rate_limit_per_minute: int = Field(default=30, alias="RECOGNITION_RATE_LIMIT_PER_MINUTE")
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str = Field(default="llama3.1", alias="LLM_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
