from pydantic import BaseModel
from typing import Optional, List


class JDCreate(BaseModel):
	title: str
	role: str
	original_text: str
	company_id: Optional[str] = None
	notes: Optional[str] = None
	tags: List[str] = []


class JDRead(BaseModel):
	id: str
	title: str
	role: str
	original_text: str
	refined_text: str | None = None
	company_id: Optional[str] = None
	notes: Optional[str] = None
	tags: List[str] = []
