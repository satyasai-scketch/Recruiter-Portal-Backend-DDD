from sqlalchemy import Column, String, JSON

from app.db.base import Base


class PersonaModel(Base):
	__tablename__ = "personas"

	id = Column(String, primary_key=True)
	job_description_id = Column(String, nullable=False, index=True)
	name = Column(String, nullable=False)
	weights = Column(JSON, nullable=False)
	intervals = Column(JSON, nullable=False)
