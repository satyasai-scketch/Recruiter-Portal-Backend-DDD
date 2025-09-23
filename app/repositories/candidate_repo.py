from typing import Optional

from app.db.session import get_session
from app.db.models.candidate import CandidateModel


class CandidateRepository:
	"""Data access for candidates (placeholder)."""

	def __init__(self):
		self.session = get_session()

	def get(self, candidate_id: str) -> Optional[CandidateModel]:
		return None

	def create(self, candidate: CandidateModel) -> CandidateModel:
		return candidate
