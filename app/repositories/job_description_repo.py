from __future__ import annotations

from typing import Optional, Sequence, Set
from app.db.models.user import UserModel
from sqlalchemy.orm import Session, joinedload, selectinload, defer
from sqlalchemy import select, func
import time

from app.db.models.job_description import JobDescriptionModel
from app.db.models.persona import PersonaModel
from app.db.models.jd_hiring_manager import JDHiringManagerMappingModel
from app.db.models.user import UserModel
from app.core.logger import logger
from app.core.authorization import get_jd_access_filter


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

	def list_by_role_id(self, db: Session, role_id: str, skip: int = 0, limit: int = 100, optimized: bool = True) -> Sequence[JobDescriptionModel]:
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
				# Defer heavy persona text fields; load creator/updater and hiring managers
				selectinload(JobDescriptionModel.personas).options(
					defer(PersonaModel.persona_notes),
					defer(PersonaModel.weights),
					defer(PersonaModel.intervals),
					joinedload(PersonaModel.creator),
					joinedload(PersonaModel.updater),
				),
				# Load hiring manager mappings and linked users
				selectinload(JobDescriptionModel.hiring_manager_mappings).joinedload(JDHiringManagerMappingModel.hiring_manager),
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

	def list_by_role_id(self, db: Session, role_id: str, skip: int = 0, limit: int = 100, optimized: bool = True) -> Sequence[JobDescriptionModel]:
		"""
		List job descriptions filtered by role_id.
		
		Args:
			db: Database session
			role_id: Job role ID to filter by
			skip: Pagination offset
			limit: Pagination limit
			optimized: Whether to use optimized query (excludes large text fields)
			
		Returns:
			Sequence of JobDescriptionModel instances filtered by role_id
		"""
		query = db.query(JobDescriptionModel).filter(JobDescriptionModel.role_id == role_id)
		
		if optimized:
			query = query.options(
				# Defer loading large text fields
				defer(JobDescriptionModel.original_text),
				defer(JobDescriptionModel.refined_text),
				defer(JobDescriptionModel.selected_text),
				# Use joinedload for many-to-one relationships
				joinedload(JobDescriptionModel.job_role),
				joinedload(JobDescriptionModel.creator),
				joinedload(JobDescriptionModel.updater),
				# Use selectinload for one-to-many relationships
				selectinload(JobDescriptionModel.personas).options(
					defer(PersonaModel.persona_notes),
					defer(PersonaModel.weights),
					defer(PersonaModel.intervals),
					joinedload(PersonaModel.creator),
					joinedload(PersonaModel.updater),
				),
				selectinload(JobDescriptionModel.hiring_manager_mappings).joinedload(JDHiringManagerMappingModel.hiring_manager),
			)
		else:
			query = query.options(
				joinedload(JobDescriptionModel.job_role),
				joinedload(JobDescriptionModel.creator),
				joinedload(JobDescriptionModel.updater),
				selectinload(JobDescriptionModel.personas).options(
					defer(PersonaModel.persona_notes),
					defer(PersonaModel.weights),
					defer(PersonaModel.intervals),
					joinedload(PersonaModel.creator),
					joinedload(PersonaModel.updater),
				),
				selectinload(JobDescriptionModel.hiring_manager_mappings).joinedload(JDHiringManagerMappingModel.hiring_manager),
			)
		
		return query.order_by(JobDescriptionModel.created_at.desc()).offset(skip).limit(limit).all()

	def count(self, db: Session) -> int:
		"""
		Optimized count query using func.count() with primary key.
		This is more efficient than .count() as it uses the primary key index
		and doesn't require a full table scan.
		"""
		result = db.query(func.count(JobDescriptionModel.id)).scalar()
		return result or 0
	
	def list_accessible(self, db: Session, user: UserModel, skip: int = 0, limit: int = 100) -> Sequence[JobDescriptionModel]:
		"""
		List JDs accessible to a user based on their role.
		
		Optimized to use SQL JOIN/subquery filtering instead of fetching all accessible IDs first.
		This is more efficient, especially for users with many accessible JDs.
		
		Args:
			db: Database session
			user: User to filter access for
			skip: Pagination offset
			limit: Pagination limit
			
		Returns:
			Sequence of accessible JobDescriptionModel instances
		"""
		query = (
			db.query(JobDescriptionModel)
			.options(
				defer(JobDescriptionModel.original_text),
				defer(JobDescriptionModel.refined_text),
				defer(JobDescriptionModel.selected_text),
				joinedload(JobDescriptionModel.job_role),
				joinedload(JobDescriptionModel.creator),
				joinedload(JobDescriptionModel.updater),
				selectinload(JobDescriptionModel.personas).options(
					defer(PersonaModel.persona_notes),
					defer(PersonaModel.weights),
					defer(PersonaModel.intervals),
					joinedload(PersonaModel.creator),
					joinedload(PersonaModel.updater),
				),
				selectinload(JobDescriptionModel.hiring_manager_mappings).joinedload(JDHiringManagerMappingModel.hiring_manager),
			)
		)
		
		# Apply access filter using SQL JOIN/subquery (more efficient than fetching all IDs)
		access_filter = get_jd_access_filter(db, user)
		if access_filter is not None:
			query = query.filter(access_filter)
		
		return query.order_by(JobDescriptionModel.created_at.desc()).offset(skip).limit(limit).all()
	
	def count_accessible(self, db: Session, user: UserModel) -> int:
		"""
		Count JDs accessible to a user based on their role.
		
		Optimized to use SQL JOIN/subquery filtering instead of fetching all accessible IDs first.
		
		Args:
			db: Database session
			user: User to filter access for
			
		Returns:
			Count of accessible JDs
		"""
		query = db.query(func.count(JobDescriptionModel.id))
		
		# Apply access filter using SQL JOIN/subquery (more efficient than fetching all IDs)
		access_filter = get_jd_access_filter(db, user)
		if access_filter is not None:
			query = query.filter(access_filter)
		
		result = query.scalar()
		return result or 0
	
	def delete(self, db: Session, jd_id: str) -> bool:
		"""Delete a job description by ID."""
		try:
			jd = self.get(db, jd_id)
			if jd:
				db.delete(jd)
				db.commit()
				return True
			return False
		except Exception as e:
			db.rollback()
			raise e
