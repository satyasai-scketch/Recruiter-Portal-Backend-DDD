from dataclasses import dataclass
from typing import List


@dataclass
class CVUploadedEvent:
	candidate_ids: List[str]


@dataclass
class ScoreRequestedEvent:
	candidate_ids: List[str]
	persona_id: str
	persona_weights: dict
