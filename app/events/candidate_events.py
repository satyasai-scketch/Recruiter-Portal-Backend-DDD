from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CVUploadedEvent:
	candidate_ids: List[str]


@dataclass
class ScoreRequestedEvent:
	candidate_ids: List[str]
	persona_id: str
	persona_weights: dict


@dataclass
class CandidateDeletedEvent:
	candidate_id: str
	candidate_name: Optional[str] = None


@dataclass
class CandidateCVDeletedEvent:
	candidate_cv_id: str
	candidate_id: str
	file_name: str