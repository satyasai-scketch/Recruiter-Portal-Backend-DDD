from __future__ import annotations

from typing import Optional, Dict, List, Tuple, Iterable
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.candidate import CandidateModel, CandidateCVModel
from app.db.models.score import ScoreModel
from app.repositories.candidate_repo import SQLAlchemyCandidateRepository
from app.repositories.candidate_cv_repo import SQLAlchemyCandidateCVRepository
from app.repositories.score_repo import SQLAlchemyScoreRepository
from app.domain.candidate import services as cand_domain_services
from app.events.event_bus import event_bus
from app.events.candidate_events import CVUploadedEvent, ScoreRequestedEvent
from app.utils.cv_utils import (
	compute_file_hash, 
	extract_file_extension, 
	extract_baseline_info,
	validate_cv_file,
	generate_s3_key
)
from app.services.storage import StorageFactory


class CandidateService:
	"""Orchestrates candidate workflows at the application layer."""

	def __init__(
		self,
		candidates: Optional[SQLAlchemyCandidateRepository] = None,
		candidate_cvs: Optional[SQLAlchemyCandidateCVRepository] = None,
		scores: Optional[SQLAlchemyScoreRepository] = None,
	):
		self.candidates = candidates or SQLAlchemyCandidateRepository()
		self.candidate_cvs = candidate_cvs or SQLAlchemyCandidateCVRepository()
		self.scores = scores or SQLAlchemyScoreRepository()

	def upload_cv(self, 
	             db: Session, 
	             file_bytes: bytes, 
	             filename: str,
	             candidate_info: Optional[Dict[str, str]] = None) -> Dict[str, any]:
		"""
		Upload CV with deduplication and versioning logic.
		
		Args:
			db: Database session
			file_bytes: File content as bytes
			filename: Original filename
			candidate_info: Optional dict with full_name, email, phone
			
		Returns:
			Dictionary with upload result:
			- status: "success", "duplicate", or "error"
			- candidate_id: ID of the candidate
			- cv_id: ID of the CV (if created)
			- file_hash: SHA256 hash of the file
			- version: CV version number
			- s3_url: S3 URL (if uploaded)
			- is_new_candidate: Whether candidate was created
			- is_new_cv: Whether CV was created
			- error: Error message (if status is "error")
		"""
		result = {
			"status": "error",
			"candidate_id": None,
			"cv_id": None,
			"file_hash": None,
			"version": None,
			"s3_url": None,
			"is_new_candidate": False,
			"is_new_cv": False,
			"error": None
		}
		
		try:
			# Step 1: Validate file
			validation = validate_cv_file(filename, len(file_bytes))
			if not validation["valid"]:
				result["error"] = validation["error"]
				return result
			
			# Step 2: Compute file hash for deduplication
			file_hash = compute_file_hash(file_bytes)
			result["file_hash"] = file_hash
			
			# Step 3: Check if file already exists (global deduplication)
			existing_cv = self.candidate_cvs.find_by_hash(db, file_hash)
			if existing_cv:
				result["status"] = "duplicate"
				result["candidate_id"] = existing_cv.candidate_id
				result["cv_id"] = existing_cv.id
				result["version"] = existing_cv.version
				result["s3_url"] = existing_cv.s3_url
				result["is_new_candidate"] = False
				result["is_new_cv"] = False
				return result
			
			# Step 4: Extract baseline info from file content
			# For now, we'll use the provided candidate_info or extract from text
			# In a real implementation, you'd parse the file content here
			baseline_info = candidate_info or {}
			
			# Step 5: Find or create candidate
			candidate = self._find_or_create_candidate(db, baseline_info)
			result["candidate_id"] = candidate.id
			result["is_new_candidate"] = (candidate.created_at == candidate.updated_at)
			
			# Step 6: Get next version for this candidate
			version = self.candidate_cvs.get_next_version(db, candidate.id)
			result["version"] = version
			
			# Step 7: Generate S3 key and upload
			extension = extract_file_extension(filename)
			s3_key = generate_s3_key(file_hash, extension)
			
			# Upload to storage (local or S3 based on configuration)
			storage_service = StorageFactory.get_storage_service()
			upload_result = storage_service.upload_file(
				file_bytes=file_bytes,
				key=s3_key,
				content_type=validation["mime_type"]
			)
			
			if not upload_result["success"]:
				result["error"] = f"Storage upload failed: {upload_result['error']}"
				return result
			
			result["s3_url"] = upload_result["url"]
			
			# Step 8: Create CV record
			cv = CandidateCVModel(
				id=str(uuid4()),
				candidate_id=candidate.id,
				file_name=filename,
				file_hash=file_hash,
				version=version,
				s3_url=upload_result["url"],
				file_size=len(file_bytes),
				mime_type=validation["mime_type"],
				status="uploaded",
				uploaded_at=datetime.now()
			)
			
			created_cv = self.candidate_cvs.create(db, cv)
			result["cv_id"] = created_cv.id
			result["is_new_cv"] = True
			
			# Step 9: Update candidate's latest_cv_id
			candidate.latest_cv_id = created_cv.id
			candidate.updated_at = datetime.now()
			self.candidates.update(db, candidate)
			
			# Step 10: Publish event
			event_bus.publish_event(CVUploadedEvent(candidate_ids=[candidate.id]))
			
			result["status"] = "success"
			return result
			
		except Exception as e:
			result["error"] = f"Unexpected error: {str(e)}"
			return result

	def _find_or_create_candidate(self, db: Session, candidate_info: Dict[str, str]) -> CandidateModel:
		"""Find existing candidate by email/phone or create new one."""
		email = candidate_info.get("email")
		phone = candidate_info.get("phone")
		
		# Try to find existing candidate
		if email or phone:
			existing = self.candidates.find_by_email_or_phone(db, email, phone)
			if existing:
				return existing
		
		# Create new candidate
		candidate = CandidateModel(
			id=str(uuid4()),
			full_name=candidate_info.get("full_name"),
			email=email,
			phone=phone,
			created_at=datetime.now(),
			updated_at=datetime.now()
		)
		
		return self.candidates.create(db, candidate)

	def upload(self, db: Session, payloads: Iterable[dict]) -> List[CandidateModel]:
		"""Legacy method - kept for backward compatibility."""
		created: List[CandidateModel] = []
		for data in (payloads or []):
			cand_agg = cand_domain_services.create_candidate(
				id=str(uuid4()),
				name=data["name"],
				email=data.get("email"),
				phone=data.get("phone"),
				years_experience=data.get("years_experience"),
				skills=data.get("skills") or [],
				education=data.get("education"),
				cv_path=data.get("cv_path"),
				summary=data.get("summary"),
			)
			model = CandidateModel(
				id=cand_agg.id,
				name=cand_agg.name,
				email=cand_agg.email,
				phone=cand_agg.phone,
				years_experience=cand_agg.years_experience,
				skills=cand_agg.skills,
				education=cand_agg.education,
				cv_path=cand_agg.cv_path,
				summary=cand_agg.summary,
				scores=cand_agg.scores,
			)
			created.append(self.candidates.create(db, model))
		# Publish a batch event with created candidate IDs
		event_bus.publish_event(CVUploadedEvent(candidate_ids=[c.id for c in created]))
		return created

	def score_candidates(
		self,
		db: Session,
		candidate_ids: List[str],
		persona_id: str,
		persona_weights: Dict[str, float],
		per_candidate_category_scores: Dict[str, Dict[str, float]],
	) -> List[ScoreModel]:
		"""Persist per-category scores and return created score rows."""
		# Publish score requested event (async workers may pick up for deeper analysis)
		event_bus.publish_event(ScoreRequestedEvent(candidate_ids=candidate_ids, persona_id=persona_id, persona_weights=persona_weights))

		rows: List[ScoreModel] = []
		for cid in candidate_ids:
			category_scores = per_candidate_category_scores.get(cid, {})
			candidate = self.candidates.get(db, cid)
			if not candidate:
				continue
			updated = cand_domain_services.score_against_persona(
				candidate,
				persona_weights,
				category_scores,
			)
			candidate.scores = updated.scores
			self.candidates.update(db, candidate)

			for category, score in (category_scores or {}).items():
				rows.append(
					ScoreModel(
						id=str(uuid4()),
						candidate_id=cid,
						persona_id=persona_id,
						category=category,
						score=float(score),
					)
				)
		return self.scores.bulk_create(db, rows)
