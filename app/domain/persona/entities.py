from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional, List


@dataclass(frozen=True)
class WeightInterval:
	"""Value object representing an allowed inclusive interval for a weight.

	Invariants are checked at construction time.
	"""

	min: float
	max: float

	def __post_init__(self) -> None:
		if not (0.0 <= self.min <= 1.0 and 0.0 <= self.max <= 1.0):
			raise ValueError("WeightInterval bounds must be within [0.0, 1.0]")
		if self.min > self.max:
			raise ValueError("WeightInterval.min must be <= WeightInterval.max")


@dataclass
class PersonaSubcategory:
	id: Optional[str]
	category_id: Optional[str]
	name: str
	weight_percentage: int
	level: Optional[str] = None


@dataclass
class PersonaCategory:
	id: Optional[str]
	persona_id: Optional[str]
	name: str
	weight_percentage: int
	subcategories: List[PersonaSubcategory]


@dataclass
class Persona:
	"""Aggregate root representing a scoring persona.

	Supports both classic weights/intervals and hierarchical categories.
	"""

	id: Optional[str]
	job_description_id: str
	name: str
	weights: Dict[str, float] | None
	intervals: Dict[str, WeightInterval] | None
	categories: List[PersonaCategory]

	def total_weight(self) -> float:
		if not self.weights:
			return float(sum(cat.weight_percentage for cat in self.categories) / 100.0)
		return float(sum(self.weights.values()))

	def with_updated_weight(self, category: str, new_weight: float) -> Persona:
		if not self.weights:
			return self
		new_weights = dict(self.weights)
		new_weights[category] = float(new_weight)
		return replace(self, weights=new_weights)
