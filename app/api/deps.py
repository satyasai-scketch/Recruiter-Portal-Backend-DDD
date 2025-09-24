from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.core.security import decode_token
from app.repositories.user_repo import SQLAlchemyUserRepository


def db_session() -> Generator[Session, None, None]:
	"""Yield a database session (placeholder)."""
	session = get_session()
	try:
		yield session
	finally:
		session.close()


# Alias preferred FastAPI convention
get_db = db_session


security = HTTPBearer(auto_error=False)


def get_current_user(
	credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
	db: Session = Depends(get_db),
):
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
	payload = decode_token(credentials.credentials)
	if not payload or "sub" not in payload:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
	user = SQLAlchemyUserRepository().get_by_id(db, payload["sub"])
	if not user or not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
	return user


def require_roles(*required_roles: str):
	def _inner(user=Depends(get_current_user)):
		roles = set(user.roles or [])
		if not set(required_roles).issubset(roles):
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
		return user
	return _inner
