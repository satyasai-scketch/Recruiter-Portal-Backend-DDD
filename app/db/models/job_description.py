from sqlalchemy import Column, String, Text

from app.db.base import Base


class JobDescriptionModel(Base):
	__tablename__ = "job_descriptions"

	id = Column(String, primary_key=True)
	title = Column(String, nullable=False)
	original_text = Column(Text, nullable=False)
	refined_text = Column(Text, nullable=True)
	company_id = Column(String, nullable=True)
