from app.repositories.job_description_repo import JobDescriptionRepository


class JDService:
	"""Orchestrates JD workflows (placeholder)."""

	def __init__(self):
		self.repo = JobDescriptionRepository()

	def create(self, data: dict) -> dict:
		return data
