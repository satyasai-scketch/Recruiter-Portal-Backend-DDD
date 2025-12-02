from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Optional, List
from datetime import datetime


class PersonaListItem(BaseModel):
	"""Minimal persona info for candidate list views"""
	persona_id: str
	persona_name: str


class CandidateCVCreate(BaseModel):
	file_name: str
	file_hash: str
	version: int
	s3_url: str
	file_size: Optional[int] = None
	mime_type: Optional[str] = None
	status: str = "uploaded"
	cv_text: Optional[str] = None
	skills: Optional[List] = None
	roles_detected: Optional[List] = None


class CandidateCVUpdate(BaseModel):
	"""Schema for updating candidate CV information"""
	status: Optional[str] = None
	cv_text: Optional[str] = None
	skills: Optional[List] = None
	roles_detected: Optional[List] = None


class CandidateCVRead(BaseModel):
	id: str
	candidate_id: str
	file_name: str
	file_hash: str
	version: int
	s3_url: str
	file_size: Optional[int] = None
	mime_type: Optional[str] = None
	status: str
	uploaded_at: datetime
	cv_text: Optional[str] = None
	skills: Optional[List] = None
	roles_detected: Optional[List] = None


class CandidateCreate(BaseModel):
	full_name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None


class CandidateUpdate(BaseModel):
	"""Schema for updating candidate information"""
	full_name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None


class CandidateRead(BaseModel):
	id: str
	full_name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None
	latest_cv_id: Optional[str] = None
	created_at: datetime
	created_by: Optional[str] = None
	created_by_name: Optional[str] = None  # Full name from creator relationship
	updated_at: Optional[datetime] = None
	updated_by: Optional[str] = None
	updated_by_name: Optional[str] = None  # Full name from updater relationship
	personas: List[PersonaListItem] = []  # Array of personas evaluated against this candidate
	cvs: Optional[List[CandidateCVRead]] = None


class CandidateUploadRequest(BaseModel):
	"""Request payload for CV upload with optional candidate identification"""
	full_name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None


class CandidateUploadResponse(BaseModel):
	"""Response for CV upload operation"""
	candidate_id: str
	cv_id: str
	file_name: str
	file_hash: str
	version: int
	s3_url: str
	status: str
	is_new_candidate: bool
	is_new_cv: bool
	cv_text: Optional[str] = None
	candidate_name: Optional[str] = None
	email: Optional[str] = None
	error: Optional[str] = None


class CandidateListResponse(BaseModel):
	"""Response for listing candidates with pagination"""
	candidates: List[CandidateRead]
	total: int
	page: int
	size: int
	has_next: bool
	has_prev: bool


class CandidateSearchRequest(BaseModel):
	"""Schema for candidate search request."""
	query: str = Field(..., description="Search term to match against candidate name, email, or phone number (partial match)")
	page: int = Field(1, ge=1, description="Page number")
	size: int = Field(10, ge=1, le=100, description="Page size")
	
	model_config = ConfigDict(from_attributes=True)


class CandidateCVListResponse(BaseModel):
	"""Response for listing candidate CVs"""
	cvs: List[CandidateCVRead]
	candidate_id: str
	total: int


class CandidateDeleteResponse(BaseModel):
	"""Response for candidate deletion"""
	message: str
	candidate_id: str


class CandidateCVDeleteResponse(BaseModel):
	"""Response for candidate CV deletion"""
	message: str
	candidate_cv_id: str
	candidate_id: str


# ========== Candidate Selection Schemas ==========

class CandidateSelectionCreate(BaseModel):
	"""Schema for creating a candidate selection"""
	candidate_id: str
	persona_id: str
	job_description_id: str
	selection_notes: Optional[str] = None
	priority: Optional[str] = Field(None, description="Priority: 'high', 'medium', or 'low'")
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionRead(BaseModel):
	"""Schema for reading a candidate selection"""
	id: str
	candidate_id: str
	persona_id: str
	job_description_id: str
	selected_by: str
	selection_notes: Optional[str] = None
	priority: Optional[str] = None
	status: str
	created_at: datetime
	updated_at: datetime
	
	# Nested candidate info
	candidate: Optional[Dict] = None  # Will be populated from relationship
	persona: Optional[Dict] = None  # Will be populated from relationship
	job_description: Optional[Dict] = None  # Will be populated from relationship
	selector: Optional[Dict] = None  # Will be populated from relationship
	
	model_config = ConfigDict(from_attributes=True)


class CandidateInfo(BaseModel):
	"""Minimal candidate information for selection responses"""
	id: str
	full_name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionItem(BaseModel):
	"""Schema for a single selection item in list responses"""
	id: str
	candidate: CandidateInfo = Field(..., description="Candidate information")
	persona_id: str
	persona_name: Optional[str] = None
	job_description_id: Optional[str] = None
	status: str
	priority: Optional[str] = None
	selection_notes: Optional[str] = None
	selected_by: Optional[str] = None
	selected_by_name: Optional[str] = None  # Full name from selector relationship
	created_at: datetime
	
	model_config = ConfigDict(from_attributes=True)


class SelectCandidatesRequest(BaseModel):
	"""Request schema for selecting multiple candidates"""
	candidate_ids: List[str] = Field(..., description="List of candidate IDs to select")
	persona_id: str
	job_description_id: str
	selection_notes: Optional[str] = None
	priority: Optional[str] = Field(None, description="Priority: 'high', 'medium', or 'low'")
	
	model_config = ConfigDict(from_attributes=True)


class SelectCandidatesResponse(BaseModel):
	"""Response schema for bulk candidate selection"""
	selected_count: int
	selections: List[CandidateSelectionItem]
	
	model_config = ConfigDict(from_attributes=True)


class SelectedCandidatesListResponse(BaseModel):
	"""Response schema for listing selected candidates"""
	selections: List[CandidateSelectionItem]
	total: int
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionUpdate(BaseModel):
	"""Schema for updating a candidate selection"""
	status: Optional[str] = Field(None, description="New status: 'selected', 'interview_scheduled', 'interviewed', 'rejected', 'hired'")
	priority: Optional[str] = Field(None, description="Priority: 'high', 'medium', or 'low'")
	selection_notes: Optional[str] = Field(None, description="Selection notes")
	change_notes: Optional[str] = Field(None, description="Optional notes about this change")
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionAuditLogRead(BaseModel):
	"""Schema for reading a candidate selection audit log entry"""
	id: str
	selection_id: str
	action: str
	changed_by: Optional[str] = None
	changed_by_name: Optional[str] = None  # Full name from changer relationship
	field_name: Optional[str] = None
	old_value: Optional[str] = None
	new_value: Optional[str] = None
	change_notes: Optional[str] = None
	created_at: datetime
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionAuditLogListResponse(BaseModel):
	"""Response schema for listing selection audit logs"""
	logs: List[CandidateSelectionAuditLogRead]
	total: int
	page: int
	size: int
	has_next: bool
	has_prev: bool
	
	model_config = ConfigDict(from_attributes=True)


class CandidateSelectionWithAuditLogsResponse(BaseModel):
	"""Response schema for selection details with audit logs"""
	selection: CandidateSelectionItem
	audit_logs: List[CandidateSelectionAuditLogRead]
	total_logs: int
	
	model_config = ConfigDict(from_attributes=True)