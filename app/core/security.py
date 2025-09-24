from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
	"""Create JWT access token for a subject (user id/email)."""
	expires_delta = timedelta(minutes=expires_minutes or settings.jwt_access_token_expires_minutes)
	to_encode = {"sub": subject, "exp": datetime.now(timezone.utc) + expires_delta}
	return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
	try:
		return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
	except Exception:
		return None
