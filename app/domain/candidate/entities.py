from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class Candidate:
	id: Optional[str]
	name: str
	cv_path: Optional[str] = None
	summary: Optional[str] = None
	scores: Optional[Dict[str, float]] = None
