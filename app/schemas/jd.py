from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class JDCreate(BaseModel):
	title: str
	role_id: str
	original_text: str
	company_id: Optional[str] = None
	notes: Optional[str] = None
	tags: List[str] = []
	# frontend may optionally send selection metadata on creation
	selected_version: Optional[str] = None
	selected_text: Optional[str] = None
	selected_edited: Optional[bool] = None
	created_by: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


class JDRead(BaseModel):
	id: str
	title: str
	role_id: str
	role_name: str
	original_text: str
	refined_text: Optional[str] = None
	company_id: Optional[str] = None
	notes: Optional[str] = None
	tags: List[str] = []
	selected_version: Optional[str] = None
	selected_text: Optional[str] = None
	selected_edited: Optional[bool] = None
	created_at: datetime
	created_by: str
	updated_at: datetime
	updated_by: Optional[str] = None
	
	# Document metadata
	original_document_filename: Optional[str] = None
	original_document_size: Optional[str] = None
	original_document_extension: Optional[str] = None
	document_word_count: Optional[str] = None
	document_character_count: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


class JDDocumentUpload(BaseModel):
	"""Schema for job description document upload."""
	title: str = Field(..., min_length=1, max_length=200, description="Job title")
	role_id: str = Field(..., description="Job role ID")
	notes: Optional[str] = Field(None, max_length=1000, description="Additional notes from recruiter")
	company_id: Optional[str] = Field(None, description="Company identifier")
	tags: List[str] = Field(default_factory=list, description="Job description tags")
	
	model_config = ConfigDict(from_attributes=True)


class JDDocumentUploadResponse(BaseModel):
	"""Response schema for document upload with extracted text."""
	id: str
	title: str
	role_id: str
	role_name: str
	original_text: str
	extracted_metadata: dict
	message: str
	
	model_config = ConfigDict(from_attributes=True)
