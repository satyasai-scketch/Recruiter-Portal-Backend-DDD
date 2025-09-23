from app.repositories.score_repo import ScoreRepository


class MatchService:
	"""Handles scoring, ranking, and recommendations (placeholder)."""

	def __init__(self):
		self.scores = ScoreRepository()

	def score(self, payload: dict) -> dict:
		return {"status": "queued", "payload": payload}
