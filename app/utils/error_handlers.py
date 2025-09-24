from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logger import logger


def handle_service_errors(exc: Exception) -> HTTPException:
	if isinstance(exc, ValueError):
		return HTTPException(status_code=400, detail=str(exc))
	if isinstance(exc, SQLAlchemyError):
		return HTTPException(status_code=500, detail="Database error")
	return HTTPException(status_code=500, detail="Internal server error")


def rollback_on_error(db: Session) -> None:
	try:
		db.rollback()
	except Exception as e:
		logger.error(f"Failed to rollback DB session: {e}")
