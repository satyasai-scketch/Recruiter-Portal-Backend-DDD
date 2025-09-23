from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


_engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False, future=True)


def get_session():
	"""Return a new SQLAlchemy session (sync placeholder)."""
	return SessionLocal()
