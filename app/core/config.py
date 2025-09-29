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
	
	# Email Configuration
	email_provider: str = "smtp"  # 'smtp', 'sendgrid', or 'aws_ses'
	
	# SMTP Configuration
	smtp_server: str = "smtp.gmail.com"
	smtp_port: int = 587
	smtp_username: str = ""
	smtp_password: str = ""
	smtp_use_tls: bool = True
	
	# SendGrid Configuration
	sendgrid_api_key: str = ""
	
	# AWS SES Configuration
	aws_access_key_id: str = ""
	aws_secret_access_key: str = ""
	aws_region: str = "us-east-1"
	
	# Common Email Settings
	from_email: str = "noreply@recruiterai.com"
	from_name: str = "Recruiter AI"
	frontend_url: str = "http://localhost:3000"

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"


settings = Settings()
