from __future__ import annotations

from typing import Optional, Dict, List, Tuple, Iterable
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.candidate import CandidateModel, CandidateCVModel
from app.db.models.score import CandidateScoreModel, ScoreStageModel, ScoreCategoryModel, ScoreSubcategoryModel, ScoreInsightModel
from app.repositories.candidate_repo import SQLAlchemyCandidateRepository
from app.repositories.candidate_cv_repo import SQLAlchemyCandidateCVRepository
from app.repositories.score_repo import SQLAlchemyScoreRepository
from app.domain.candidate import services as cand_domain_services
from app.events.event_bus import event_bus
from app.events.candidate_events import CVUploadedEvent, ScoreRequestedEvent, ScoreCompletedEvent, CandidateDeletedEvent, CandidateCVDeletedEvent
from app.utils.cv_utils import (
	compute_file_hash, 
	extract_file_extension, 
	validate_cv_file,
	generate_s3_key
)
from app.utils.cv_extraction import extract_baseline_info_with_timing
from app.utils.document_parser import DocumentParser
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
			"cv_text": None,
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
				result["cv_text"] = existing_cv.cv_text  # Include existing CV text
				return result
			
			# Step 4: Extract baseline info from file content
			baseline_info = candidate_info or {}
			
			# Extract text from CV file for storage and baseline info extraction
			extracted_text = ""
			try:
				# Extract text from the CV file
				parsed_doc = DocumentParser.extract_text(filename, file_bytes)
				extracted_text = parsed_doc.get("extracted_text", "")
				
				# If no candidate info provided, extract baseline info from text
				if not baseline_info.get("email") or not baseline_info.get("phone"):
					# Extract baseline info (name, email, phone) from text with timing
					extraction_result = extract_baseline_info_with_timing(extracted_text)
					
					# Log extraction performance
					print(f"CV extraction completed using {extraction_result.approach} approach in {extraction_result.processing_time_ms:.2f}ms")
					if not extraction_result.success:
						print(f"CV extraction failed: {extraction_result.error}")
					
					# Merge extracted info with provided info (provided info takes precedence)
					if not baseline_info.get("full_name") and extraction_result.name:
						baseline_info["full_name"] = extraction_result.name
					if not baseline_info.get("email") and extraction_result.email:
						baseline_info["email"] = extraction_result.email
					if not baseline_info.get("phone") and extraction_result.phone:
						baseline_info["phone"] = extraction_result.phone
						
			except Exception as e:
				# If text extraction fails, continue with provided info only
				print(f"Warning: Failed to extract text from CV {filename}: {e}")
				extracted_text = ""  # Ensure extracted_text is empty string on failure
			
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
				cv_text=extracted_text,  # Store the complete extracted text
				uploaded_at=datetime.now()
			)
			
			created_cv = self.candidate_cvs.create(db, cv)
			result["cv_id"] = created_cv.id
			result["is_new_cv"] = True
			result["cv_text"] = extracted_text  # Include the extracted text in the response
			
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


	def score_candidate(
		self,
		db: Session,
		candidate_id: str,
		persona_id: str,
		cv_id: str,
		ai_scoring_response: Dict[str, any],
		scoring_version: str = "v1.0",
		processing_time_ms: Optional[int] = None
	) -> CandidateScoreModel:
		"""Create comprehensive scoring record from AI response."""
		score_id = str(uuid4())
		
		# Extract main scoring data
		pipeline_stage_reached = ai_scoring_response.get("pipeline_stage_reached", 3)
		final_score = float(ai_scoring_response.get("final_score", 0.0))
		final_decision = ai_scoring_response.get("final_decision", "UNKNOWN")
		
		# Extract score progression
		score_progression = ai_scoring_response.get("score_progression", {})
		embedding_score = score_progression.get("embedding")
		lightweight_llm_score = score_progression.get("lightweight_llm")
		detailed_llm_score = score_progression.get("detailed_llm")
		
		# Create main score record
		score_record = CandidateScoreModel(
			id=score_id,
			candidate_id=candidate_id,
			persona_id=persona_id,
			cv_id=cv_id,
			pipeline_stage_reached=pipeline_stage_reached,
			final_score=final_score,
			final_decision=final_decision,
			embedding_score=float(embedding_score) if embedding_score is not None else None,
			lightweight_llm_score=float(lightweight_llm_score) if lightweight_llm_score is not None else None,
			detailed_llm_score=float(detailed_llm_score) if detailed_llm_score is not None else None,
			scoring_version=scoring_version,
			processing_time_ms=processing_time_ms
		)
		
		# Create stage records
		for stage_num in range(1, pipeline_stage_reached + 1):
			stage_key = f"stage{stage_num}"
			stage_data = ai_scoring_response.get(stage_key, {})
			
			if stage_data:
				stage_record = ScoreStageModel(
					id=str(uuid4()),
					candidate_score_id=score_id,
					stage_number=stage_num,
					method=stage_data.get("method", ""),
					model=stage_data.get("model"),
					score=float(stage_data.get("score", 0.0)),
					threshold=float(stage_data.get("threshold")) if stage_data.get("threshold") is not None else None,
					min_threshold=float(stage_data.get("min_threshold")) if stage_data.get("min_threshold") is not None else None,
					decision=stage_data.get("decision", ""),
					reason=stage_data.get("reason"),
					next_stage=stage_data.get("next_stage"),
					relevance_score=stage_data.get("relevance_score"),
					quick_assessment=stage_data.get("quick_assessment"),
					skills_detected=stage_data.get("skills"),
					roles_detected=stage_data.get("roles_detected"),
					key_matches=stage_data.get("key_matches"),
					key_gaps=stage_data.get("key_gaps")
				)
				score_record.score_stages.append(stage_record)
		
		# Create category records
		stage3_data = ai_scoring_response.get("stage3", {})
		categories_data = stage3_data.get("categories", [])
		
		for cat_data in categories_data:
			category_record = ScoreCategoryModel(
				id=str(uuid4()),
				candidate_score_id=score_id,
				category_name=cat_data.get("name", ""),
				weight_percentage=int(cat_data.get("weight", 0)),
				category_score_percentage=float(cat_data.get("category_score_percentage", 0.0)),
				category_contribution=float(cat_data.get("category_contribution", 0.0))
			)
			score_record.categories.append(category_record)
			
			# Create subcategory records
			subcategories_data = cat_data.get("subcategories", [])
			for subcat_data in subcategories_data:
				subcategory_record = ScoreSubcategoryModel(
					id=str(uuid4()),
					category_id=category_record.id,
					subcategory_name=subcat_data.get("name", ""),
					weight_percentage=int(subcat_data.get("weight", 0)),
					expected_level=int(subcat_data.get("expected_level", 0)),
					actual_level=int(subcat_data.get("actual_level", 0)),
					base_score=float(subcat_data.get("base_score", 0.0)),
					missing_count=int(subcat_data.get("missing_count", 0)),
					scored_percentage=float(subcat_data.get("scored_percentage", 0.0)),
					notes=subcat_data.get("notes")
				)
				category_record.subcategories.append(subcategory_record)
		
		# Create insight records (strengths and gaps)
		strengths = stage3_data.get("strengths", [])
		for strength in strengths:
			insight_record = ScoreInsightModel(
				id=str(uuid4()),
				candidate_score_id=score_id,
				insight_type="STRENGTH",
				insight_text=strength
			)
			score_record.insights.append(insight_record)
		
		gaps = stage3_data.get("gaps", [])
		for gap in gaps:
			insight_record = ScoreInsightModel(
				id=str(uuid4()),
				candidate_score_id=score_id,
				insight_type="GAP",
				insight_text=gap
			)
			score_record.insights.append(insight_record)
		
		# Save the complete score record
		created_score = self.scores.create_candidate_score(db, score_record)
		
		# Publish score completed event
		event_bus.publish_event(ScoreCompletedEvent(
			score_id=created_score.id,
			candidate_id=candidate_id,
			persona_id=persona_id,
			cv_id=cv_id,
			final_score=float(created_score.final_score),
			final_decision=created_score.final_decision,
			pipeline_stage_reached=created_score.pipeline_stage_reached
		))
		
		return created_score

	def get_by_id(self, db: Session, candidate_id: str) -> Optional[CandidateModel]:
		"""Get a candidate by ID."""
		return self.candidates.get(db, candidate_id)

	def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[CandidateModel]:
		"""Get all candidates with pagination."""
		return list(self.candidates.list_all(db)[skip:skip + limit])

	def update_candidate(self, db: Session, candidate_id: str, update_data: Dict[str, any]) -> Optional[CandidateModel]:
		"""Update candidate information."""
		try:
			candidate = self.candidates.get(db, candidate_id)
			if not candidate:
				return None
			
			# Update only provided fields
			for field, value in update_data.items():
				if hasattr(candidate, field) and value is not None:
					setattr(candidate, field, value)
			
			# Update timestamp
			candidate.updated_at = datetime.now()
			
			# Save changes
			updated_candidate = self.candidates.update(db, candidate)
			return updated_candidate
			
		except Exception as e:
			db.rollback()
			raise e

	def update_candidate_cv(self, db: Session, cv_id: str, update_data: Dict[str, any]) -> Optional[CandidateCVModel]:
		"""Update candidate CV information."""
		try:
			cv = self.candidate_cvs.get(db, cv_id)
			if not cv:
				return None
			
			# Update only provided fields
			for field, value in update_data.items():
				if hasattr(cv, field) and value is not None:
					setattr(cv, field, value)
			
			# Save changes
			updated_cv = self.candidate_cvs.update(db, cv)
			return updated_cv
			
		except Exception as e:
			db.rollback()
			raise e

	def get_candidate_cv(self, db: Session, candidate_cv_id: str) -> Optional[CandidateCVModel]:
		"""Get a candidate CV by ID."""
		return self.candidate_cvs.get(db, candidate_cv_id)

	def get_candidate_cvs(self, db: Session, candidate_id: str) -> List[CandidateCVModel]:
		"""Get all CVs for a specific candidate."""
		return self.candidate_cvs.get_candidate_cvs(db, candidate_id)

	def get_candidate_score(self, db: Session, score_id: str) -> Optional[CandidateScoreModel]:
		"""Get a specific candidate score by ID."""
		return self.scores.get_candidate_score(db, score_id)

	def list_candidate_scores(self, db: Session, candidate_id: str, skip: int = 0, limit: int = 100) -> List[CandidateScoreModel]:
		"""List all scores for a candidate."""
		return list(self.scores.list_candidate_scores(db, candidate_id, skip, limit))

	def list_scores_for_candidate_persona(self, db: Session, candidate_id: str, persona_id: str, skip: int = 0, limit: int = 100) -> List[CandidateScoreModel]:
		"""List scores for a candidate against a specific persona."""
		return list(self.scores.list_scores_for_candidate_persona(db, candidate_id, persona_id)[skip:skip + limit])

	def list_scores_for_cv_persona(self, db: Session, cv_id: str, persona_id: str, skip: int = 0, limit: int = 100) -> List[CandidateScoreModel]:
		"""List scores for a CV against a specific persona."""
		return list(self.scores.list_scores_for_cv_persona(db, cv_id, persona_id)[skip:skip + limit])

	def list_all_scores(self, db: Session, skip: int = 0, limit: int = 100) -> List[CandidateScoreModel]:
		"""List all scores with pagination."""
		return list(self.scores.list_all_scores(db, skip, limit))

	def delete_candidate(self, db: Session, candidate_id: str) -> bool:
		"""Delete a candidate and all associated CVs and scores."""
		try:
			# Get candidate first to check if it exists and get name for event
			candidate = self.candidates.get(db, candidate_id)
			if not candidate:
				return False
			
			candidate_name = candidate.full_name
			
			# Delete all scores for this candidate first
			# This handles orphaned scores that might exist due to missing foreign key constraints
			scores = db.query(CandidateScoreModel).filter(CandidateScoreModel.candidate_id == candidate_id).all()
			for score in scores:
				# Delete all related score data (stages, categories, insights)
				# These should cascade automatically due to foreign key constraints
				db.delete(score)
			
			# Delete all CVs for this candidate
			cvs = self.candidate_cvs.get_candidate_cvs(db, candidate_id)
			for cv in cvs:
				# Delete CV from storage
				try:
					storage_service = StorageFactory.get_storage_service()
					# Generate the same key format used during upload
					extension = extract_file_extension(cv.file_name)
					storage_key = generate_s3_key(cv.file_hash, extension)
					storage_service.delete_file(storage_key)
				except Exception as e:
					# Log storage deletion error but continue with DB deletion
					print(f"Failed to delete CV file from storage: {e}")
				
				# Delete CV from database
				self.candidate_cvs.delete(db, cv.id)
			
			# Delete candidate
			success = self.candidates.delete(db, candidate_id)
			
			if success:
				# Publish event
				try:
					event_bus.publish_event(CandidateDeletedEvent(
						candidate_id=candidate_id,
						candidate_name=candidate_name
					))
				except Exception as e:
					print(f"Failed to publish CandidateDeletedEvent: {e}")
			
			return success
			
		except Exception as e:
			db.rollback()
			raise e

	def delete_candidate_cv(self, db: Session, candidate_cv_id: str) -> bool:
		"""Delete a specific candidate CV."""
		try:
			# Get CV first to check if it exists and get info for event
			cv = self.candidate_cvs.get(db, candidate_cv_id)
			if not cv:
				return False
			
			candidate_id = cv.candidate_id
			file_name = cv.file_name
			
			# Delete CV from storage
			try:
				storage_service = StorageFactory.get_storage_service()
				# Generate the same key format used during upload
				extension = extract_file_extension(cv.file_name)
				storage_key = generate_s3_key(cv.file_hash, extension)
				storage_service.delete_file(storage_key)
			except Exception as e:
				# Log storage deletion error but continue with DB deletion
				print(f"Failed to delete CV file from storage: {e}")
			
			# Delete CV from database
			success = self.candidate_cvs.delete(db, candidate_cv_id)
			
			if success:
				# Update candidate's latest_cv_id if this was the latest CV
				candidate = self.candidates.get(db, candidate_id)
				if candidate and candidate.latest_cv_id == candidate_cv_id:
					# Find the next latest CV
					remaining_cvs = self.candidate_cvs.get_candidate_cvs(db, candidate_id)
					if remaining_cvs:
						candidate.latest_cv_id = remaining_cvs[0].id  # First one is latest due to desc ordering
					else:
						candidate.latest_cv_id = None
					candidate.updated_at = datetime.now()
					self.candidates.update(db, candidate)
				
				# Publish event
				try:
					event_bus.publish_event(CandidateCVDeletedEvent(
						candidate_cv_id=candidate_cv_id,
						candidate_id=candidate_id,
						file_name=file_name
					))
				except Exception as e:
					print(f"Failed to publish CandidateCVDeletedEvent: {e}")
			
			return success
			
		except Exception as e:
			db.rollback()
			raise e