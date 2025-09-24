from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class JobDescriptionModel(Base):
	__tablename__ = "job_descriptions"

	id = Column(String, primary_key=True)
	title = Column(String, nullable=False)
	role = Column(String, nullable=False)
	original_text = Column(Text, nullable=False)
	refined_text = Column(Text, nullable=True)
	final_text = Column(Text, nullable=True)
	company_id = Column(String, nullable=True)
	notes = Column(Text, nullable=True)
	tags = Column(JSON, nullable=False, default=list)

	# Relationships
	personas = relationship("PersonaModel", back_populates="job_description", cascade="all, delete-orphan")
