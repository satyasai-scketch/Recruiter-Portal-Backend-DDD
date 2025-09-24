from sqlalchemy import Column, String, Float
from sqlalchemy.dialects.sqlite import JSON

from app.db.base import Base


class CandidateModel(Base):
	__tablename__ = "candidates"

	id = Column(String, primary_key=True)
	name = Column(String, nullable=False)
	email = Column(String, nullable=True)
	phone = Column(String, nullable=True)
	years_experience = Column(Float, nullable=True)
	skills = Column(JSON, nullable=False, default=list)
	education = Column(String, nullable=True)
	cv_path = Column(String, nullable=True)
	summary = Column(String, nullable=True)
	scores = Column(JSON, nullable=True)
