from typing import Optional

from app.db.session import get_session
from app.db.models.job_description import JobDescriptionModel


class JobDescriptionRepository:
	"""Data access for job descriptions (placeholder)."""

	def __init__(self):
		self.session = get_session()

	def get(self, jd_id: str) -> Optional[JobDescriptionModel]:
		return None

	def create(self, jd: JobDescriptionModel) -> JobDescriptionModel:
		return jd
