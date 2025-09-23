from sqlalchemy import Column, String, JSON

from app.db.base import Base


class CandidateModel(Base):
	__tablename__ = "candidates"

	id = Column(String, primary_key=True)
	name = Column(String, nullable=False)
	cv_path = Column(String, nullable=True)
	summary = Column(String, nullable=True)
	scores = Column(JSON, nullable=True)
