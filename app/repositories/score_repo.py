from typing import List

from app.db.session import get_session
from app.db.models.score import ScoreModel


class ScoreRepository:
	"""Data access for scores (placeholder)."""

	def __init__(self):
		self.session = get_session()

	def bulk_create(self, scores: List[ScoreModel]) -> List[ScoreModel]:
		return scores
