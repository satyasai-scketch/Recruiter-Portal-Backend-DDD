from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional


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
class Persona:
	"""Aggregate root representing a scoring persona.

	A persona defines category weights that should generally sum to 1.0, and
	optional acceptable intervals per category to guide recruiter edits.
	"""

	id: Optional[str]
	job_description_id: str
	name: str
	weights: Dict[str, float]
	intervals: Dict[str, WeightInterval]

	def total_weight(self) -> float:
		"""Return the sum of all category weights."""
		return float(sum(self.weights.values()))

	def get_interval(self, category: str) -> Optional[WeightInterval]:
		"""Return the interval for a category if defined."""
		return self.intervals.get(category)

	def is_within_interval(self, category: str, value: float) -> bool:
		"""Check whether a weight value is within the category's interval if any.

		If no interval is defined for the category, returns True.
		"""
		interval = self.get_interval(category)
		if interval is None:
			return True
		return interval.min <= value <= interval.max

	def with_updated_weight(self, category: str, new_weight: float) -> Persona:
		"""Return a new persona with the specified category weight updated."""
		new_weights = dict(self.weights)
		new_weights[category] = float(new_weight)
		return replace(self, weights=new_weights)
