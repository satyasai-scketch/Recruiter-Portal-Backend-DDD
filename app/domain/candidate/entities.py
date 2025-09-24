from __future__ import annotations

from dataclasses import dataclass, replace, field
from typing import Dict, Optional, List


@dataclass
class Candidate:
	"""Aggregate root representing a candidate profile within the domain.

	This aggregate is independent of persistence and frameworks. It captures
	attributes that influence scoring against personas (e.g., skills and
	experience) and stores per-category scores when evaluated.
	"""

	id: Optional[str]
	name: str
	email: Optional[str] = None
	phone: Optional[str] = None
	years_experience: Optional[float] = None
	skills: List[str] = field(default_factory=list)
	education: Optional[str] = None
	cv_path: Optional[str] = None
	summary: Optional[str] = None
	scores: Optional[Dict[str, float]] = None  # category -> score in [0,1]

	def with_added_skill(self, skill: str) -> Candidate:
		"""Return a new candidate with the given skill appended if not present."""
		skill_norm = (skill or "").strip().lower()
		if not skill_norm:
			return self
		if skill_norm in (s.lower() for s in self.skills):
			return self
		return replace(self, skills=[*self.skills, skill])

	def with_scores(self, new_scores: Dict[str, float]) -> Candidate:
		"""Return a new candidate with per-category scores replaced."""
		return replace(self, scores=dict(new_scores or {}))
