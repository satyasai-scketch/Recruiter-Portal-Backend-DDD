from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Optional

from app.domain.candidate.rules import clamp_score, jaccard_similarity


@dataclass
class ParsedCV:
	name: Optional[str]
	emails: List[str]
	phones: List[str]
	years_experience: float
	education: List[str]
	skills: List[str]
	summary: Optional[str]


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
YEAR_RE = re.compile(r"(\d+)\s*(\+)?\s*(years|yrs|year)\b", flags=re.I)
EDU_KEYWORDS = ["bachelor", "master", "phd", "diploma", "b.tech", "m.tech", "bsc", "msc"]
SKILL_SEPS = re.compile(r"[,/\n;]\s*|\t")


def parse_cv(text: str) -> ParsedCV:
	"""Deterministically parse common CV fields from raw text.

	This is a heuristic, regex-based parser intended for a first pass.
	"""
	emails = EMAIL_RE.findall(text)
	phones = PHONE_RE.findall(text)
	years = [int(m.group(1)) for m in YEAR_RE.finditer(text)]
	years_experience = float(max(years) if years else 0)

	lower = text.lower()
	education = [kw for kw in EDU_KEYWORDS if kw in lower]
	# Primitive skills extraction: take lines containing 'skills' and split
	skills: List[str] = []
	for line in text.splitlines():
		if "skill" in line.lower():
			for token in SKILL_SEPS.split(line):
				t = token.strip()
				if len(t) > 1 and not t.lower().startswith("skill"):
					skills.append(t)

	name = None
	summary = None
	first_line = text.strip().splitlines()[0] if text.strip().splitlines() else None
	if first_line and 3 <= len(first_line) <= 80 and "@" not in first_line:
		name = first_line.strip()
	# crude summary: first paragraph
	paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
	if paragraphs:
		summary = paragraphs[0][:400]

	return ParsedCV(
		name=name,
		emails=list(dict.fromkeys(emails)),
		phones=list(dict.fromkeys(phones)),
		years_experience=years_experience,
		education=education,
		skills=list(dict.fromkeys(skills)),
		summary=summary,
	)


def score_parsed_cv(parsed: ParsedCV, persona_categories: List[str], role_keywords: List[str]) -> Dict[str, float]:
	"""Deterministically compute per-category scores from parsed fields.

	- Technical: skill overlap + years normalization
	- Cognitive: proxy via education keywords and summary length
	- Behavioral: proxy via presence of team/lead words
	- Values: neutral baseline
	- Communication: proxy via summary length band
	- Leadership: proxy via leadership terms and years
	"""
	lower_summary = (parsed.summary or "").lower()
	skills_norm = [s.lower() for s in parsed.skills]
	role_norm = [r.lower() for r in role_keywords]

	scores: Dict[str, float] = {}

	if "Technical" in persona_categories:
		overlap = jaccard_similarity(skills_norm, role_norm)
		years_factor = clamp_score(parsed.years_experience / 10.0)
		scores["Technical"] = clamp_score(0.7 * overlap + 0.3 * years_factor)

	if "Cognitive" in persona_categories:
		edu_factor = clamp_score(len(parsed.education) / 3.0)
		sum_factor = clamp_score(len(lower_summary) / 400.0)
		scores["Cognitive"] = clamp_score(0.6 * edu_factor + 0.4 * sum_factor)

	if "Behavioral" in persona_categories:
		flags = ["team", "collaborat", "mentor", "stakeholder", "agile", "scrum"]
		flag_hits = sum(1 for f in flags if f in lower_summary)
		scores["Behavioral"] = clamp_score(flag_hits / 4.0)

	if "Values" in persona_categories:
		values_flags = ["inclusion", "divers", "ethic", "sustain", "mission", "customer"]
		flag_hits = sum(1 for f in values_flags if f in lower_summary)
		scores["Values"] = clamp_score(0.2 + 0.2 * flag_hits)

	if "Communication" in persona_categories:
		length = len(lower_summary)
		if length < 80:
			scores["Communication"] = 0.3
		elif length < 200:
			scores["Communication"] = 0.6
		else:
			scores["Communication"] = 0.8

	if "Leadership" in persona_categories:
		lead_flags = ["lead", "manage", "direct", "head", "own"]
		lead_hits = sum(1 for f in lead_flags if f in lower_summary)
		years_factor = clamp_score(parsed.years_experience / 12.0)
		scores["Leadership"] = clamp_score(0.6 * (lead_hits / 3.0) + 0.4 * years_factor)

	return scores
