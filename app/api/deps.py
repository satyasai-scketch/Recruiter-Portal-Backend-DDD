from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.core.security import decode_token
from app.repositories.user_repo import SQLAlchemyUserRepository
from app.services.mfa_service import MFAService
from app.core.config import settings
from app.core.context import request_db_session, request_user_id


def db_session() -> Generator[Session, None, None]:
	"""Yield a database session and set it in context."""
	session = get_session()
	try:
		# Set session in context for LLM tracing
		request_db_session.set(session)
		yield session
	finally:
		session.close()
		# Clear context after request
		request_db_session.set(None)


# Alias preferred FastAPI convention
get_db = db_session


security = HTTPBearer(auto_error=False)


def get_current_user(
	credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
	db: Session = Depends(get_db),
):
	"""Get current user and set user_id in context for LLM tracing."""
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
	payload = decode_token(credentials.credentials)
	if not payload or "sub" not in payload:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
	user = SQLAlchemyUserRepository().get_by_id(db, payload["sub"])
	if not user or not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
	
	# Set user_id in context for LLM tracing
	request_user_id.set(user.id)
	
	return user


def require_roles(*required_roles: str):
	def _inner(user=Depends(get_current_user)):
		user_role_name = (user.role.name if getattr(user, "role", None) else None)
		if user_role_name is None or user_role_name not in set(required_roles):
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
		return user
	return _inner


def require_mfa(user=Depends(get_current_user), db: Session = Depends(get_db)):
	"""Dependency that requires MFA to be enabled and verified for the user."""
	if not settings.mfa_enabled:
		return user
	
	mfa_service = MFAService()
	mfa_status = mfa_service.get_mfa_status(db, user.id)
	
	if not mfa_status["enabled"]:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, 
			detail="Multi-factor authentication is required but not enabled for this user"
		)
	
	if not mfa_status["totp_verified"]:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, 
			detail="Multi-factor authentication is not verified for this user"
		)
	
	return user


def optional_mfa(user=Depends(get_current_user), db: Session = Depends(get_db)):
	"""Dependency that checks MFA status but doesn't require it."""
	if not settings.mfa_enabled:
		return {"user": user, "mfa_enabled": False, "mfa_verified": False}
	
	mfa_service = MFAService()
	mfa_status = mfa_service.get_mfa_status(db, user.id)
	
	return {
		"user": user, 
		"mfa_enabled": mfa_status["enabled"], 
		"mfa_verified": mfa_status["totp_verified"]
	}
