from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Dict, Optional, Tuple

from app.utils.rag_utils import VectorIndex, retrieve_best_practices
from app.utils.embeddings import EmbeddingsClient
from app.domain.job_description import services as jd_domain
from app.domain.persona import services as persona_domain
from app.domain.persona.entities import WeightInterval
from app.domain.candidate import rules as cand_rules


# Protocols for dependency injection
class SmallLLM(Protocol):
	def generate(self, prompt: str) -> str:
		...


class LargeLLM(Protocol):
	def generate(self, prompt: str) -> str:
		...


@dataclass
class JDRefinementInput:
	role: str
	original_text: str
	company_id: Optional[str] = None
	notes: Optional[str] = None


def refine_jd_workflow(
	inp: JDRefinementInput,
	template_index: VectorIndex,
	small_llm: SmallLLM,
) -> str:
	"""Refine JD using template retrieval + best practices + small LLM.

	This function is a stub; it assembles a prompt using retrieved templates and
	best practices. It does not implement complex logic.
	"""
	templates = template_index.search(inp.role, top_k=2)
	best_practices = retrieve_best_practices(inp.role)
	prompt = (
		"Refine the following Job Description using the provided templates and best practices.\n\n"
		f"ROLE: {inp.role}\n"
		f"COMPANY_ID: {inp.company_id or ''}\n"
		f"NOTES: {inp.notes or ''}\n\n"
		f"TEMPLATES:\n{chr(10).join(templates)}\n\n"
		f"BEST_PRACTICES:\n- " + "\n- ".join(best_practices) + "\n\n"
		f"ORIGINAL_JD:\n{inp.original_text}\n\n"
		"Return only the refined JD text."
	)
	return small_llm.generate(prompt)


@dataclass
class PersonaCreationInput:
	job_description_id: str
	role: str
	name: str
	weights: Optional[Dict[str, float]] = None


def create_persona_workflow(
	inp: PersonaCreationInput,
	archetype_index: VectorIndex,
	small_llm: SmallLLM,
) -> Tuple[Dict[str, float], Dict[str, WeightInterval]]:
	"""Create a persona from archetype + adjust with small LLM (stub)."""
	archetypes = archetype_index.search(inp.role, top_k=1)
	base_weights = persona_domain.DEFAULT_SCHEMA if inp.weights is None else inp.weights
	prompt = (
		"You are a hiring assistant. Given an archetype and JD role, adjust the weights.\n"
		f"ROLE: {inp.role}\n"
		f"ARCHETYPE: {archetypes[0] if archetypes else ''}\n"
		f"BASE_WEIGHTS: {base_weights}\n"
		"Return JSON mapping of category to weight between 0 and 1 summing to ~1."
	)
	_ = small_llm.generate(prompt)  # In real code, parse JSON; here we keep base
	weights = base_weights
	intervals = {
		k: WeightInterval(max(0.0, v - 0.1), min(1.0, v + 0.1)) for k, v in weights.items()
	}
	return weights, intervals


PREWRITTEN_WARNINGS: Dict[str, str] = {
	"Technical_low": "Lowering Technical below recommended may exclude core skill matches.",
	"Cognitive_low": "Cognitive below range could reduce problem-solving emphasis.",
	"Values_low": "Values below range may weaken culture alignment.",
	"Behavioral_low": "Behavioral below range may overlook collaboration and communication.",
}


def weightage_warnings(weights: Dict[str, float], intervals: Dict[str, WeightInterval]) -> List[str]:
	"""Return human-readable warnings for out-of-interval weights.

	This uses deterministic rules and prewritten messages; no LLM required.
	"""
	violations: List[str] = []
	for cat, value in (weights or {}).items():
		interval = intervals.get(cat)
		if not interval:
			continue
		if not (interval.min <= float(value) <= interval.max):
			key = f"{cat}_low" if float(value) < interval.min else f"{cat}_high"
			msg = PREWRITTEN_WARNINGS.get(key, f"{cat} weight {value} outside recommended range {interval.min}-{interval.max}.")
			violations.append(msg)
	return violations


@dataclass
class CVAnalysisInput:
	candidate_text: str
	persona_weights: Dict[str, float]
	persona_categories: List[str]


def analyze_cv_workflow(
	inp: CVAnalysisInput,
	embeddings: EmbeddingsClient,
	vector_index: VectorIndex,
	small_llm: SmallLLM,
	large_llm: LargeLLM,
) -> Dict[str, float]:
	"""Mixed pipeline: deterministic parsing + embeddings + selective LLM.

	This is a stub pipeline that demonstrates control flow:
	1) Deterministic parsing (simulate with simple heuristics)
	2) Embedding similarity retrieval for each category
	3) Small LLM for borderline scores
	4) Large LLM for top candidates when deeper analysis is required
	"""
	# 1) Deterministic parsing heuristic
	skill_tokens = [t.strip().lower() for t in inp.candidate_text.split() if len(t) > 2]

	# 2) Embedding similarity (stub): retrieve category exemplars
	category_scores: Dict[str, float] = {}
	for cat in inp.persona_categories:
		refs = vector_index.search(cat, top_k=3)
		_ = embeddings.embed([inp.candidate_text] + refs)
		# Simulate similarity with token overlap
		ref_tokens = {r.lower() for r in refs}
		score = cand_rules.clamp_score(len(ref_tokens & set(skill_tokens)) / max(1, len(ref_tokens) or 1))
		category_scores[cat] = score

	# 3) Small LLM for borderline categories
	for cat, score in list(category_scores.items()):
		if 0.35 <= score <= 0.6:
			prompt = f"Rate relevance of candidate text to category '{cat}' from 0 to 1. Text: {inp.candidate_text[:2000]}"
			resp = small_llm.generate(prompt)
			try:
				llm_score = float(resp.strip())
			except Exception:
				llm_score = score
			category_scores[cat] = cand_rules.clamp_score((score + llm_score) / 2)

	# 4) Large LLM for deeper analysis if overall is near threshold
	total = cand_rules.compute_weighted_score(category_scores, inp.persona_weights)
	if 0.65 <= total <= 0.75:
		prompt = "Provide a brief, evidence-based assessment focusing on edge alignment."
		_ = large_llm.generate(prompt)

	return category_scores
