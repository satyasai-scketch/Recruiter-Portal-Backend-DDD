from app.repositories.candidate_repo import CandidateRepository


class CandidateService:
	"""Orchestrates candidate workflows (placeholder)."""

	def __init__(self):
		self.repo = CandidateRepository()

	def upload(self, data: dict) -> dict:
		return data
