from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func

from app.db.base import Base


class CandidateModel(Base):
	__tablename__ = "candidates"

	id = Column(String, primary_key=True)
	full_name = Column(String, nullable=True)
	email = Column(String, nullable=True, index=True)
	phone = Column(String, nullable=True, index=True)
	latest_cv_id = Column(String, ForeignKey("candidate_cvs.id"), nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
	updated_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

	cvs = relationship("CandidateCVModel", back_populates="candidate", cascade="all, delete-orphan", foreign_keys="[CandidateCVModel.candidate_id]")
	latest_cv = relationship("CandidateCVModel", foreign_keys="[CandidateModel.latest_cv_id]", post_update=True)
	creator = relationship("UserModel", foreign_keys=[created_by])
	updater = relationship("UserModel", foreign_keys=[updated_by])


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
	uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	uploaded_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

	# reserved for later enrichment
	cv_text = Column(String, nullable=True)       # complete extracted text from CV
	skills = Column(JSON, nullable=True)          # list of strings or structured
	roles_detected = Column(JSON, nullable=True)  # list of strings

	candidate = relationship("CandidateModel", back_populates="cvs", foreign_keys="[CandidateCVModel.candidate_id]")
	uploader = relationship("UserModel", foreign_keys=[uploaded_by])


class CandidateSelectionModel(Base):
	__tablename__ = "candidate_selections"

	id = Column(String, primary_key=True)
	candidate_id = Column(String, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
	persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
	job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
	selected_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
	
	# Selection Metadata
	selection_notes = Column(Text, nullable=True)
	priority = Column(String, nullable=True)  # 'high', 'medium', 'low'
	
	# Status
	status = Column(String, nullable=False, default="selected")  # 'selected', 'interview_scheduled', 'interviewed', 'rejected', 'hired'
	
	# Audit Fields
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
	
	# Relationships
	candidate = relationship("CandidateModel", foreign_keys=[candidate_id])
	persona = relationship("PersonaModel", foreign_keys=[persona_id])
	job_description = relationship("JobDescriptionModel", foreign_keys=[job_description_id])
	selector = relationship("UserModel", foreign_keys=[selected_by])
	
	# Table constraints
	__table_args__ = (
		UniqueConstraint("candidate_id", "persona_id", name="uq_candidate_persona_selection"),
		Index("idx_candidate_selections_candidate", "candidate_id"),
		Index("idx_candidate_selections_persona", "persona_id"),
		Index("idx_candidate_selections_status", "status"),
		Index("idx_candidate_selections_jd", "job_description_id"),
	)
	
	# Relationship to audit logs
	audit_logs = relationship("CandidateSelectionAuditLogModel", back_populates="selection", cascade="all, delete-orphan", order_by="CandidateSelectionAuditLogModel.created_at")


class CandidateSelectionAuditLogModel(Base):
	"""Audit log for tracking all changes to candidate selections."""
	__tablename__ = "candidate_selection_audit_logs"
	
	id = Column(String, primary_key=True)
	selection_id = Column(String, ForeignKey("candidate_selections.id", ondelete="CASCADE"), nullable=False, index=True)
	
	# Change tracking
	action = Column(String, nullable=False)  # 'created', 'updated', 'status_changed', 'notes_updated', 'priority_updated'
	changed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
	
	# Field changes (stored as JSON for flexibility)
	field_name = Column(String, nullable=True)  # 'status', 'priority', 'selection_notes', etc.
	old_value = Column(Text, nullable=True)  # Previous value
	new_value = Column(Text, nullable=True)  # New value
	
	# Additional context
	change_notes = Column(Text, nullable=True)  # Optional notes about the change
	
	# Timestamp
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	
	# Relationships
	selection = relationship("CandidateSelectionModel", back_populates="audit_logs", foreign_keys=[selection_id])
	changer = relationship("UserModel", foreign_keys=[changed_by])
	
	# Table constraints
	__table_args__ = (
		Index("idx_selection_audit_selection", "selection_id"),
		Index("idx_selection_audit_changed_by", "changed_by"),
		Index("idx_selection_audit_created_at", "created_at"),
	)