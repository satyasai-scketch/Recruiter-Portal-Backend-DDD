from __future__ import annotations

from typing import Iterable, List, Tuple


def validate_title_length(title: str, min_len: int = 2, max_len: int = 120) -> bool:
	"""Validate that the job title length is within acceptable bounds.

	Args:
		title: The job title string to validate.
		min_len: Minimum allowed length for a valid title.
		max_len: Maximum allowed length for a valid title.

	Returns:
		True if the title length is within [min_len, max_len], otherwise False.

	Rationale:
		Overly short titles lack clarity, and overly long titles reduce readability.
	"""
	if title is None:
		return False
	length = len(title.strip())
	return min_len <= length <= max_len


def validate_text_presence(text: str, min_len: int = 50) -> bool:
	"""Validate that a JD text is present and meets a minimal length threshold.

	Args:
		text: Raw job description text.
		min_len: Minimum character count to be considered substantive.

	Returns:
		True if text is non-empty and above the threshold; False otherwise.

	Rationale:
		Ensures that downstream refinement has sufficient signal to operate on.
	"""
	if text is None:
		return False
	return len(text.strip()) >= min_len


def detect_missing_sections(text: str, required_sections: Iterable[str]) -> List[str]:
	"""Detect which required sections are missing from the JD text.

	Args:
		text: The JD body to inspect.
		required_sections: Section headers/keywords expected in a well-formed JD
			(e.g., ["Responsibilities", "Requirements", "Benefits"]).

	Returns:
		A list of section names that are not present in the JD text.

	Rationale:
		Used to drive low-cost, deterministic guidance before invoking LLMs.
	"""
	lower_text = text.lower()
	missing: List[str] = []
	for section in required_sections:
		if section.lower() not in lower_text:
			missing.append(section)
	return missing


def compute_diff_against_template(jd_text: str, template_text: str) -> List[Tuple[str, str]]:
	"""Compute a high-level diff between JD text and a template.

	Args:
		jd_text: The recruiter's provided JD text.
		template_text: The canonical template text used as a reference.

	Returns:
		A list of (status, fragment) tuples where status is one of
		"missing" | "extra" | "present" indicating the relationship
		between JD and template for coarse-grained guidance.

	Rationale:
		This rule allows a lightweight gap analysis to inform refinement prompts.
	"""
	# Very coarse token presence comparison (placeholder domain rule)
	jd_tokens = set(token for token in jd_text.lower().split() if token)
	tpl_tokens = set(token for token in template_text.lower().split() if token)

	missing = sorted(list(tpl_tokens - jd_tokens))
	extra = sorted(list(jd_tokens - tpl_tokens))
	present = sorted(list(jd_tokens & tpl_tokens))

	result: List[Tuple[str, str]] = []
	result.extend(("missing", tok) for tok in missing)
	result.extend(("extra", tok) for tok in extra)
	result.extend(("present", tok) for tok in present)
	return result


def validate_tags(tags: Iterable[str], max_tags: int = 20, max_len: int = 40) -> bool:
	"""Validate tags used to annotate the JD aggregate.

	Args:
		tags: Iterable of tag strings.
		max_tags: Maximum number of tags allowed.
		max_len: Maximum length for any individual tag.

	Returns:
		True if tags are within bounds and syntactically valid; False otherwise.

	Rationale:
		Tags are used for quick filtering and retrieval. Limits prevent noise.
	"""
	t = list(tags or [])
	if len(t) > max_tags:
		return False
	for tag in t:
		if not tag or not tag.strip() or len(tag.strip()) > max_len:
			return False
	return True
