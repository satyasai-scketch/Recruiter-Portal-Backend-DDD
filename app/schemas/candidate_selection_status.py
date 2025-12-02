# app/schemas/candidate_selection_status.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CandidateSelectionStatusBase(BaseModel):
	"""Base schema for candidate selection status data."""
	code: str = Field(..., min_length=1, max_length=50, description="Status code (e.g., 'selected', 'interview_scheduled')")
	name: str = Field(..., min_length=1, max_length=100, description="Display name (e.g., 'Selected', 'Interview Scheduled')")
	description: Optional[str] = Field(None, max_length=500, description="Status description")
	display_order: int = Field(0, description="Order for dropdown display")


class CandidateSelectionStatusCreate(CandidateSelectionStatusBase):
	"""Schema for creating a new candidate selection status."""
	is_active: bool = Field(True, description="Whether the status is active")


class CandidateSelectionStatusUpdate(BaseModel):
	"""Schema for updating candidate selection status information."""
	code: Optional[str] = Field(None, min_length=1, max_length=50, description="Status code")
	name: Optional[str] = Field(None, min_length=1, max_length=100, description="Display name")
	description: Optional[str] = Field(None, max_length=500, description="Status description")
	display_order: Optional[int] = Field(None, description="Order for dropdown display")
	is_active: Optional[bool] = Field(None, description="Whether the status is active")


class CandidateSelectionStatusRead(CandidateSelectionStatusBase):
	"""Schema for reading candidate selection status information."""
	id: str
	is_active: bool
	created_at: datetime
	created_by: Optional[str] = None
	updated_at: datetime
	updated_by: Optional[str] = None
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionStatusListResponse(BaseModel):
	"""Schema for candidate selection status list response."""
	statuses: List[CandidateSelectionStatusRead]
	total: int
	page: int
	size: int
	has_next: bool
	has_prev: bool


class CandidateSelectionStatusSimple(BaseModel):
	"""Simplified status schema for dropdowns and basic selection."""
	id: str
	code: str
	name: str
	display_order: int
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionStatusResponse(BaseModel):
	"""Schema for status operation response."""
	message: str
	status: Optional[CandidateSelectionStatusRead] = None

