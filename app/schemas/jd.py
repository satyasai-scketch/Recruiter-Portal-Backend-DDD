from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class JDCreate(BaseModel):
	title: str
	role: str
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
	role: str
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

	model_config = ConfigDict(from_attributes=True)
