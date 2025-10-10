from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class CandidateModel(Base):
	__tablename__ = "candidates"

	id = Column(String, primary_key=True)
	full_name = Column(String, nullable=True)
	email = Column(String, nullable=True, index=True)
	phone = Column(String, nullable=True, index=True)
	latest_cv_id = Column(String, ForeignKey("candidate_cvs.id"), nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow)

	cvs = relationship("CandidateCVModel", back_populates="candidate", cascade="all, delete-orphan")


class CandidateCVModel(Base):
	__tablename__ = "candidate_cvs"

	id = Column(String, primary_key=True)
	candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False, index=True)
	file_name = Column(String, nullable=False)
	file_hash = Column(String, nullable=False, unique=True, index=True)  # global dedup
	version = Column(Integer, nullable=False)  # per-candidate version (1..n)
	s3_url = Column(String, nullable=False)
	file_size = Column(Integer, nullable=True)
	mime_type = Column(String, nullable=True)
	status = Column(String, nullable=False, default="uploaded")  # uploaded|pending|failed|parsed
	uploaded_at = Column(DateTime, default=datetime.utcnow)

	# reserved for later enrichment
	skills = Column(JSON, nullable=True)          # list of strings or structured
	roles_detected = Column(JSON, nullable=True)  # list of strings

	candidate = relationship("CandidateModel", back_populates="cvs")
