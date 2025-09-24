from __future__ import annotations

from typing import Dict, Iterable, Tuple, List


def validate_category_names(categories: Iterable[str], min_categories: int = 2, max_categories: int = 20) -> bool:
	"""Validate category name collection size and syntax.

	Args:
		categories: Iterable of category names (e.g., "Technical", "Cognitive").
		min_categories: Minimum number of categories required.
		max_categories: Maximum number of categories allowed.

	Returns:
		True if the number of categories is within bounds and names are non-empty.

	Rationale:
		Personas should contain a reasonable number of well-formed categories.
	"""
	names = [c.strip() for c in categories if c is not None]
	if not (min_categories <= len(names) <= max_categories):
		return False
	return all(len(n) > 0 for n in names)


def validate_weights_range(weights: Dict[str, float]) -> bool:
	"""Validate that each category weight is within [0.0, 1.0].

	Args:
		weights: Mapping of category -> weight.

	Returns:
		True if all weights are in range; False otherwise.

	Rationale:
		Individual category weights represent proportions and must be bounded.
	"""
	for value in (weights or {}).values():
		if not (0.0 <= float(value) <= 1.0):
			return False
	return True


def validate_weights_sum(weights: Dict[str, float], tolerance: float = 1e-6) -> bool:
	"""Validate that the sum of weights is approximately 1.0.

	Args:
		weights: Mapping of category -> weight.
		tolerance: Numerical tolerance for floating point comparisons.

	Returns:
		True if the sum is within tolerance of 1.0; False otherwise.

	Rationale:
		Weights should form a convex combination to compute a weighted score.
	"""
	total = float(sum((weights or {}).values()))
	return abs(total - 1.0) <= tolerance


def detect_out_of_interval(weights: Dict[str, float], intervals: Dict[str, Tuple[float, float]]) -> List[str]:
	"""Return categories whose weight lies outside the recommended interval.

	Args:
		weights: Mapping of category -> weight.
		intervals: Mapping of category -> (min, max) inclusive bounds.

	Returns:
		List of category names that violate their intervals. If a category has no
		interval defined, it is considered within bounds.

	Rationale:
		Supports UX warnings without requiring an LLM call.
	"""
	violations: List[str] = []
	for cat, w in (weights or {}).items():
		if cat not in intervals:
			continue
		min_v, max_v = intervals[cat]
		if not (min_v <= float(w) <= max_v):
			violations.append(cat)
	return violations


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
	"""Return a new weights mapping scaled to sum to 1.0.

	Args:
		weights: Mapping of category -> raw weight values.

	Returns:
		New mapping with values scaled by the total sum. If total is zero,
		returns the original mapping unchanged.

	Rationale:
		Handy for turning arbitrary positive weights into proper proportions.
	"""
	total = float(sum((weights or {}).values()))
	if total <= 0.0:
		return dict(weights or {})
	return {k: float(v) / total for k, v in (weights or {}).items()}
