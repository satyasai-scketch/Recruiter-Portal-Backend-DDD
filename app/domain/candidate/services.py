from __future__ import annotations

from typing import Dict, Iterable, Optional

from app.domain.candidate.entities import Candidate
from app.domain.candidate import rules as cand_rules


def create_candidate(
	*,
	id: Optional[str],
	name: str,
	email: Optional[str] = None,
	phone: Optional[str] = None,
	years_experience: Optional[float] = None,
	skills: Iterable[str] | None = None,
	education: Optional[str] = None,
	cv_path: Optional[str] = None,
	summary: Optional[str] = None,
) -> Candidate:
	"""Factory for a Candidate aggregate with validation.

	Raises ValueError if minimal identity/contact requirements are not met.
	"""
	if not cand_rules.validate_contact(name, email, phone):
		raise ValueError("Invalid candidate identity/contact information")
	return Candidate(
		id=id,
		name=name.strip(),
		email=email.strip() if email else None,
		phone=phone.strip() if phone else None,
		years_experience=float(years_experience) if years_experience is not None else None,
		skills=[s for s in (skills or [])],
		education=education,
		cv_path=cv_path,
		summary=summary,
		scores=None,
	)


def add_skills(candidate: Candidate, new_skills: Iterable[str]) -> Candidate:
	"""Return a new Candidate with the given skills added (deduplicated)."""
	result = candidate
	for s in (new_skills or []):
		result = result.with_added_skill(s)
	return result


def fit_band(candidate: Candidate, low_threshold: float = 0.4, high_threshold: float = 0.7) -> str:
	"""Return 'low' | 'mid' | 'high' fit band based on candidate total score."""
	total = 0.0
	if candidate.scores and "__total__" in candidate.scores:
		total = float(candidate.scores["__total__"])
	return cand_rules.band_fit(total, low_threshold=low_threshold, high_threshold=high_threshold)
