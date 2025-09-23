from dataclasses import dataclass
from typing import Optional


@dataclass
class JobDescription:
	id: Optional[str]
	title: str
	original_text: str
	refined_text: Optional[str] = None
	company_id: Optional[str] = None
