from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy.orm import Session

from app.db.models.job_description import JobDescriptionModel


class JobDescriptionRepository:
	"""Repository interface for JobDescription aggregates."""

	def get(self, db: Session, jd_id: str) -> Optional[JobDescriptionModel]:
		raise NotImplementedError

	def create(self, db: Session, jd: JobDescriptionModel) -> JobDescriptionModel:
		raise NotImplementedError

	def update(self, db: Session, jd: JobDescriptionModel) -> JobDescriptionModel:
		raise NotImplementedError

	def list_by_company(self, db: Session, company_id: str) -> Sequence[JobDescriptionModel]:
		raise NotImplementedError


class SQLAlchemyJobDescriptionRepository(JobDescriptionRepository):
	"""SQLAlchemy-backed implementation of JobDescriptionRepository."""

	def get(self, db: Session, jd_id: str) -> Optional[JobDescriptionModel]:
		return db.get(JobDescriptionModel, jd_id)

	def create(self, db: Session, jd: JobDescriptionModel) -> JobDescriptionModel:
		db.add(jd)
		db.commit()
		db.refresh(jd)
		return jd

	def update(self, db: Session, jd: JobDescriptionModel) -> JobDescriptionModel:
		db.add(jd)
		db.commit()
		db.refresh(jd)
		return jd

	def list_by_company(self, db: Session, company_id: str) -> Sequence[JobDescriptionModel]:
		return (
			db.query(JobDescriptionModel)
			.filter(JobDescriptionModel.company_id == company_id)
			.order_by(JobDescriptionModel.title.asc())
			.all()
		)
