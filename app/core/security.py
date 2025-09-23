from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.core.config import settings


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
	"""Create JWT access token (placeholder)."""
	expires_delta = timedelta(minutes=expires_minutes or settings.jwt_access_token_expires_minutes)
	to_encode = {"sub": subject, "exp": datetime.now(timezone.utc) + expires_delta}
	return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> bool:
	"""Validate JWT token (placeholder)."""
	try:
		jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
		return True
	except Exception:
		return False
