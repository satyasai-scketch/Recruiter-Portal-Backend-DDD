from sqlalchemy import Column, String, Float

from app.db.base import Base


class ScoreModel(Base):
	__tablename__ = "scores"

	id = Column(String, primary_key=True)
	candidate_id = Column(String, nullable=False, index=True)
	persona_id = Column(String, nullable=False, index=True)
	category = Column(String, nullable=False)
	score = Column(Float, nullable=False)
