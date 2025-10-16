# Command: ScoreCandidate

from .base import Command


class ScoreCandidate(Command):
	"""Command to score a single candidate against a persona using comprehensive AI scoring."""
	
	def __init__(self, candidate_id: str, persona_id: str, cv_id: str, ai_scoring_response: dict, scoring_version: str = "v1.0", processing_time_ms: int = None):
		self.candidate_id = candidate_id
		self.persona_id = persona_id
		self.cv_id = cv_id
		self.ai_scoring_response = ai_scoring_response
		self.scoring_version = scoring_version
		self.processing_time_ms = processing_time_ms
