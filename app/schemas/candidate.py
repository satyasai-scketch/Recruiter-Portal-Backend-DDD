from pydantic import BaseModel
from typing import Dict, Optional, List


class CandidateCreate(BaseModel):
	name: str
	email: Optional[str] = None
	phone: Optional[str] = None
	years_experience: Optional[float] = None
	skills: List[str] = []
	education: Optional[str] = None
	cv_path: Optional[str] = None
	summary: Optional[str] = None


class CandidateRead(BaseModel):
	id: str
	name: str
	email: Optional[str] = None
	phone: Optional[str] = None
	years_experience: Optional[float] = None
	skills: List[str] = []
	education: Optional[str] = None
	cv_path: Optional[str] = None
	summary: Optional[str] = None
	scores: Optional[Dict[str, float]] = None
