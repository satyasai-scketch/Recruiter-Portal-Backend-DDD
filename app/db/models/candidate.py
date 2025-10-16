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
	created_at = Column(DateTime, default=datetime.now)
	updated_at = Column(DateTime, default=datetime.now)

	cvs = relationship("CandidateCVModel", back_populates="candidate", cascade="all, delete-orphan", foreign_keys="[CandidateCVModel.candidate_id]")
	latest_cv = relationship("CandidateCVModel", foreign_keys="[CandidateModel.latest_cv_id]", post_update=True)


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
	uploaded_at = Column(DateTime, default=datetime.now)

	# reserved for later enrichment
	cv_text = Column(String, nullable=True)       # complete extracted text from CV
	skills = Column(JSON, nullable=True)          # list of strings or structured
	roles_detected = Column(JSON, nullable=True)  # list of strings

	candidate = relationship("CandidateModel", back_populates="cvs", foreign_keys="[CandidateCVModel.candidate_id]")
