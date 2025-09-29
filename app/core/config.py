from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	"""Application settings loaded from environment variables."""

	app_name: str = "Recruiter AI Backend"
	environment: str = "development"
	api_prefix: str = "/api/v1"

	# Database
	database_url: str = "sqlite:///./app.db"

	# Security
	jwt_secret_key: str = "change-me"
	jwt_algorithm: str = "HS256"
	jwt_access_token_expires_minutes: int = 60

	# Workers / Queue
	redis_url: str = "redis://localhost:6379/0"

	# Embeddings / Models (placeholders)
	embedding_model_name: str = "all-MiniLM-L6-v2"

	OPENAI_API_KEY: str = ""
	PINECONE_API_KEY: str = ""

	# Vector Database Configuration
	VECTOR_INDEX_NAME: str = "jd-templates-v1"
	EMBEDDING_MODEL: str = "text-embedding-3-small"
	EMBEDDING_DIMENSION: int = 1536

	# Storage Configuration
	JD_STORAGE_FILE: str = "data\jd_storage.json"
	TEMPLATE_DATA_DIR: str = "data\jd_templates"

	# Search Configuratio
	DEFAULT_MIN_SIMILARITY: float = 0.5
	MAX_SEARCH_RESULTS: int = 10

	# Pinecone Configuration
	PINECONE_CLOUD: str = "aws"
	PINECONE_REGION: str = "us-east-1"

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"


settings = Settings()
