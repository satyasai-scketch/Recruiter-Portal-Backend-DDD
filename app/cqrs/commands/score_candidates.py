# Command: ScoreCandidates

from .base import Command


class ScoreCandidates(Command):
	"""Command to score candidates against a persona."""
	
	def __init__(self, candidate_ids: list[str], persona_id: str, persona_weights: dict, per_candidate_scores: dict):
		self.candidate_ids = candidate_ids
		self.persona_id = persona_id
		self.persona_weights = persona_weights
		self.per_candidate_scores = per_candidate_scores
