from pydantic import BaseModel
from typing import Dict, Optional


class CandidateCreate(BaseModel):
	name: str
	cv_path: Optional[str] = None


class CandidateRead(BaseModel):
	id: str
	name: str
	cv_path: Optional[str] = None
	summary: Optional[str] = None
	scores: Optional[Dict[str, float]] = None
