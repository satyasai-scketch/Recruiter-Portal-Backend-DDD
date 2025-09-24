from __future__ import annotations

from typing import Dict, Iterable, Tuple


def validate_contact(name: str, email: str | None, phone: str | None, min_name_len: int = 2) -> bool:
	"""Validate basic candidate identity/contact information.

	Args:
		name: Candidate's display name.
		email: Optional email string.
		phone: Optional phone string.
		min_name_len: Minimum length for the candidate name.

	Returns:
		True if name is long enough and at least one contact method is present.

	Rationale:
		Ensures candidates are identifiable and contactable.
	"""
	if name is None or len(name.strip()) < min_name_len:
		return False
	if (email is None or not email.strip()) and (phone is None or not phone.strip()):
		return False
	return True


def clamp_score(value: float) -> float:
	"""Clamp an arbitrary numeric value into the [0.0, 1.0] range.

	Rationale:
		Useful for normalizing partial or heuristic scores into a standard band.
	"""
	return max(0.0, min(1.0, float(value)))


def compute_weighted_score(category_scores: Dict[str, float], weights: Dict[str, float]) -> float:
	"""Compute a deterministic weighted score from per-category scores.

	Args:
		category_scores: Mapping of category -> score in [0,1].
		weights: Mapping of category -> weight that sums to ~1.0.

	Returns:
		Weighted sum across the intersection of categories present in both inputs.

	Rationale:
		Scoring should be transparent, deterministic, and auditable.
	"""
	total = 0.0
	for cat, w in (weights or {}).items():
		if cat in (category_scores or {}):
			total += float(category_scores[cat]) * float(w)
	return clamp_score(total)


def band_fit(score: float, low_threshold: float = 0.4, high_threshold: float = 0.7) -> str:
	"""Classify a total score into 'low', 'mid', or 'high' fit bands.

	Args:
		score: Total weighted score in [0,1].
		low_threshold: Score below this is 'low'.
		high_threshold: Score equal or above this is 'high'. Others are 'mid'.

	Returns:
		One of 'low', 'mid', 'high'.

	Rationale:
		Creates a simple, transparent banding rule for recruiter-facing UI.
	"""
	s = clamp_score(score)
	if s < low_threshold:
		return "low"
	if s >= high_threshold:
		return "high"
	return "mid"


def jaccard_similarity(a: Iterable[str], b: Iterable[str]) -> float:
	"""Compute Jaccard similarity between two skill sets.

	Args:
		a: First iterable of tokens (e.g., skills).
		b: Second iterable of tokens (e.g., skills).

	Returns:
		Similarity score in [0,1] based on set intersection over union.

	Rationale:
		A cheap heuristic for skill overlap before any embedding/LLM steps.
	"""
	set_a = {s.strip().lower() for s in a if s and s.strip()}
	set_b = {s.strip().lower() for s in b if s and s.strip()}
	if not set_a and not set_b:
		return 0.0
	intersection = len(set_a & set_b)
	union = len(set_a | set_b)
	return clamp_score(intersection / union if union else 0.0)
