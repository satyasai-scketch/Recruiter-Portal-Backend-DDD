from typing import Generator

from app.db.session import get_session


def db_session() -> Generator:
	"""Yield a database session (placeholder)."""
	session = get_session()
	try:
		yield session
	finally:
		session.close()
