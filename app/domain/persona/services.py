from __future__ import annotations

from typing import Dict, Iterable, Optional

from app.domain.persona.entities import Persona, WeightInterval
from app.domain.persona import rules as persona_rules


DEFAULT_SCHEMA: Dict[str, float] = {
	"Technical": 0.40,
	"Cognitive": 0.20,
	"Values": 0.20,
	"Behavioral": 0.20,
}


def create_persona(
	*,
	id: Optional[str],
	job_description_id: str,
	name: str,
	weights: Dict[str, float] | None = None,
	intervals: Dict[str, WeightInterval] | None = None,
	normalize: bool = True,
) -> Persona:
	"""Factory for Persona aggregate with validation.

	Args:
		id: Optional persona id (not persisted here).
		job_description_id: Associated job description id.
		name: Persona display name.
		weights: Category weights; if None, uses DEFAULT_SCHEMA.
		intervals: Optional per-category allowed intervals.
		normalize: If True, scale weights to sum to 1.0.

	Returns:
		Persona instance with validated invariants.
	"""
	w = dict(weights or DEFAULT_SCHEMA)
	names_ok = persona_rules.validate_category_names(w.keys())
	ranges_ok = persona_rules.validate_weights_range(w)
	if normalize:
		w = persona_rules.normalize_weights(w)
	sum_ok = persona_rules.validate_weights_sum(w)
	if not (names_ok and ranges_ok and sum_ok):
		raise ValueError("Invalid persona weights or categories")

	ival = dict(intervals or {})
	return Persona(
		id=id,
		job_description_id=job_description_id,
		name=name.strip(),
		weights=w,
		intervals=ival,
	)


def update_weight(persona: Persona, *, category: str, value: float, enforce_interval: bool = False) -> Persona:
	"""Return a new Persona with a single category weight updated.

	If `enforce_interval` is True and the new value falls outside the category's
	interval, a ValueError is raised. Sum normalization is not performed here to
	preserve the user's intent; callers can normalize separately if needed.
	"""
	if not (0.0 <= float(value) <= 1.0):
		raise ValueError("Weight must be within [0.0, 1.0]")
	if enforce_interval and not persona.is_within_interval(category, float(value)):
		raise ValueError(f"Value {value} outside recommended interval for '{category}'")
	return persona.with_updated_weight(category, float(value))


def normalize_persona(persona: Persona) -> Persona:
	"""Return a new Persona with weights normalized to sum to 1.0."""
	new_weights = persona_rules.normalize_weights(persona.weights)
	return Persona(
		id=persona.id,
		job_description_id=persona.job_description_id,
		name=persona.name,
		weights=new_weights,
		intervals=dict(persona.intervals),
	)


def detect_interval_warnings(persona: Persona) -> list[str]:
	"""Return category names whose current weights violate their intervals."""
	intervals_tuple = {k: (v.min, v.max) for k, v in (persona.intervals or {}).items()}
	return persona_rules.detect_out_of_interval(persona.weights, intervals_tuple)
