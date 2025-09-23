from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	"""Application settings loaded from environment variables."""

	app_name: str = "Recruiter AI Backend"
	environment: str = "development"
	api_prefix: str = "/api/v1"

	# Database
	database_url: str = "sqlite+aiosqlite:///./app.db"

	# Security
	jwt_secret_key: str = "change-me"
	jwt_algorithm: str = "HS256"
	jwt_access_token_expires_minutes: int = 60

	# Workers / Queue
	redis_url: str = "redis://localhost:6379/0"

	# Embeddings / Models (placeholders)
	embedding_model_name: str = "all-MiniLM-L6-v2"

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"


settings = Settings()
