from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime


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


class CandidateRead(BaseModel):
	id: str
	full_name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None
	latest_cv_id: Optional[str] = None
	created_at: datetime
	updated_at: datetime
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


class CandidateListResponse(BaseModel):
	"""Response for listing candidates with pagination"""
	candidates: List[CandidateRead]
	total: int
	page: int
	size: int
	has_next: bool
	has_prev: bool


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