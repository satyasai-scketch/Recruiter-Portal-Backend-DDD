from pydantic import BaseModel


class ScoreCreate(BaseModel):
	candidate_id: str
	persona_id: str
	category: str
	score: float


class ScoreRead(BaseModel):
	id: str
	candidate_id: str
	persona_id: str
	category: str
	score: float
