from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional

from app.domain.job_description.entities import JobDescription, JobRole, RefinementNotes
from app.domain.job_description import rules as jd_rules


def create_job_description(
	*,
	id: Optional[str],
	title: str,
	role_name: str,
	original_text: str,
	company_id: Optional[str] = None,
	notes_text: Optional[str] = None,
	tags: Iterable[str] | None = None,
) -> JobDescription:
	"""Factory for `JobDescription` aggregate with basic validation.

	This service enforces simple invariants via rules and constructs the aggregate
	without any persistence or framework concerns.
	"""
	if not jd_rules.validate_title_length(title):
		raise ValueError("Invalid title length")
	if not jd_rules.validate_text_presence(original_text):
		raise ValueError("Original text too short or empty")
	if tags and not jd_rules.validate_tags(tags):
		raise ValueError("Invalid tags")

	role = JobRole(role_name)
	company = None
	if company_id:
		from app.domain.job_description.entities import CompanyProfileRef

		company = CompanyProfileRef(company_id)
	notes = RefinementNotes(notes_text or "") if notes_text is not None else None

	return JobDescription(
		id=id,
		title=title.strip(),
		role=role,
		original_text=original_text.strip(),
		refined_text=None,
		company=company,
		notes=notes,
		tags=list(tags or []),
	)


def prepare_refinement_brief(
	jd: JobDescription,
	required_sections: Iterable[str],
	template_text: Optional[str] = None,
) -> dict:
	"""Produce a lightweight refinement brief for downstream small-model usage.

	The brief summarizes detected issues and optional template diffs to guide
	cost-effective refinement prompts outside the domain layer.
	"""
	missing = jd_rules.detect_missing_sections(jd.original_text, required_sections)
	diff = []
	if template_text:
		diff = jd_rules.compute_diff_against_template(jd.original_text, template_text)
	return {
		"title": jd.title,
		"role": jd.role.name,
		"missing_sections": missing,
		"template_diff": diff,
		"notes": jd.notes.text if jd.notes else "",
	}


def apply_refinement(jd: JobDescription, refined_text: str) -> JobDescription:
	"""Return a new `JobDescription` with the given refined text applied.

	This function is pure and returns a new instance (does not mutate input).
	Validation is kept minimal to ensure refined text is substantive.
	"""
	if not jd_rules.validate_text_presence(refined_text, min_len=50):
		raise ValueError("Refined text too short or empty")
	return replace(jd, refined_text=refined_text.strip())
