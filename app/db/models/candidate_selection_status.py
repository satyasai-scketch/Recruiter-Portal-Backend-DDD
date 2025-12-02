from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class CandidateSelectionStatusModel(Base):
	"""Model for candidate selection statuses (lookup table)"""
	__tablename__ = "candidate_selection_statuses"

	id = Column(String, primary_key=True)
	code = Column(String, nullable=False, unique=True, index=True)  # e.g., 'selected', 'interview_scheduled'
	name = Column(String, nullable=False)  # Display name e.g., 'Selected', 'Interview Scheduled'
	description = Column(Text, nullable=True)  # Optional description
	display_order = Column(Integer, nullable=False, default=0)  # Order for dropdown display
	is_active = Column(String, nullable=False, default="true")  # Store as string for SQLite compatibility
	
	# Audit fields
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
	updated_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	
	# Relationships
	creator = relationship("UserModel", foreign_keys=[created_by])
	updater = relationship("UserModel", foreign_keys=[updated_by])

