from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CVUploadedEvent:
	candidate_ids: List[str]


@dataclass
class ScoreRequestedEvent:
	candidate_id: str
	persona_id: str
	cv_id: str
	scoring_version: str = "v1.0"


@dataclass
class ScoreCompletedEvent:
	score_id: str
	candidate_id: str
	persona_id: str
	cv_id: str
	final_score: float
	final_decision: str
	pipeline_stage_reached: int


@dataclass
class CandidateDeletedEvent:
	candidate_id: str
	candidate_name: Optional[str] = None


@dataclass
class CandidateCVDeletedEvent:
	candidate_cv_id: str
	candidate_id: str
	file_name: str