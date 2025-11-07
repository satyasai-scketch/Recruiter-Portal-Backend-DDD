from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy.orm import Session, joinedload, selectinload, defer
from sqlalchemy import select, func
import time

from app.db.models.job_description import JobDescriptionModel
from app.db.models.persona import PersonaModel
from app.db.models.user import UserModel
from app.core.logger import logger


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

	def list_all(self, db: Session) -> Sequence[JobDescriptionModel]:
		raise NotImplementedError

	def list_by_creator(self, db: Session, user_id: str) -> Sequence[JobDescriptionModel]:
		raise NotImplementedError

	def count(self, db: Session) -> int:
		raise NotImplementedError


class SQLAlchemyJobDescriptionRepository(JobDescriptionRepository):
	"""SQLAlchemy-backed implementation of JobDescriptionRepository."""

	def get(self, db: Session, jd_id: str) -> Optional[JobDescriptionModel]:
		return db.query(JobDescriptionModel).options(joinedload(JobDescriptionModel.job_role)).filter(JobDescriptionModel.id == jd_id).first()

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
			.order_by(JobDescriptionModel.created_at.desc())
			.all()
		)

	def list_all(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[JobDescriptionModel]:
		return db.query(JobDescriptionModel).options(joinedload(JobDescriptionModel.job_role)).order_by(JobDescriptionModel.created_at.desc()).offset(skip).limit(limit).all()
	
	def list_all_optimized(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[JobDescriptionModel]:
		"""
		Optimized query for listing JDs that efficiently loads relationships.
		Key optimizations:
		1. Uses selectinload for personas to avoid cartesian product (joinedload creates duplicates)
		2. Defers loading large text fields (original_text, refined_text, selected_text)
		3. Uses joinedload for many-to-one relationships (job_role, creator)
		
		This should be significantly faster than the previous implementation.
		"""
		return (
			db.query(JobDescriptionModel)
			.options(
				# Defer loading large text fields - they won't be loaded unless accessed
				defer(JobDescriptionModel.original_text),
				defer(JobDescriptionModel.refined_text),
				defer(JobDescriptionModel.selected_text),
				# Use joinedload for many-to-one relationships (efficient, no duplicates)
				joinedload(JobDescriptionModel.job_role),
				joinedload(JobDescriptionModel.creator),
				joinedload(JobDescriptionModel.updater),
				# Use selectinload for one-to-many relationships to avoid cartesian product
				# This loads personas in a separate query with IN clause, much faster
				selectinload(JobDescriptionModel.personas),
			)
			.order_by(JobDescriptionModel.created_at.desc())
			.offset(skip)
			.limit(limit)
			.all()
		)

	def list_by_creator(self, db: Session, user_id: str) -> Sequence[JobDescriptionModel]:
		return (
			db.query(JobDescriptionModel)
			.options(joinedload(JobDescriptionModel.job_role))
			.filter(JobDescriptionModel.created_by == user_id)
			.order_by(JobDescriptionModel.created_at.desc())
			.all()
		)

	def count(self, db: Session) -> int:
		"""
		Optimized count query using func.count() with primary key.
		This is more efficient than .count() as it uses the primary key index
		and doesn't require a full table scan.
		"""
		result = db.query(func.count(JobDescriptionModel.id)).scalar()
		return result or 0
