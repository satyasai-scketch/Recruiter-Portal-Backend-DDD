from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class WeightInterval:
	min: float
	max: float


@dataclass
class Persona:
	id: Optional[str]
	job_description_id: str
	name: str
	weights: Dict[str, float]
	intervals: Dict[str, WeightInterval]
