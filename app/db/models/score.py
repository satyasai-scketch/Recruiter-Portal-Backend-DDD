from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, DECIMAL, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CandidateScoreModel(Base):
	"""Main score record for a candidate scored against a persona with a specific CV."""
	__tablename__ = "candidate_scores"

	id = Column(String, primary_key=True)
	candidate_id = Column(String, nullable=False, index=True)
	persona_id = Column(String, nullable=False, index=True)
	cv_id = Column(String, ForeignKey("candidate_cvs.id", ondelete="CASCADE"), nullable=False, index=True)
	
	# Overall scoring results
	pipeline_stage_reached = Column(Integer, nullable=False)  # 1, 2, or 3
	final_score = Column(DECIMAL(5, 2), nullable=False)  # 0.00 to 100.00
	final_decision = Column(String, nullable=False)  # STRONG_FIT, MODERATE_FIT, WEAK_FIT, etc.
	
	# Score progression through stages
	embedding_score = Column(DECIMAL(5, 2), nullable=True)  # Stage 1 score
	lightweight_llm_score = Column(DECIMAL(5, 2), nullable=True)  # Stage 2 score
	detailed_llm_score = Column(DECIMAL(5, 2), nullable=True)  # Stage 3 score
	
	# Metadata
	scored_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	scoring_version = Column(String, nullable=True)  # Track scoring algorithm version
	processing_time_ms = Column(Integer, nullable=True)  # Performance tracking
	
	# Relationships
	cv = relationship("CandidateCVModel", foreign_keys=[cv_id])
	score_stages = relationship("ScoreStageModel", back_populates="candidate_score", cascade="all, delete-orphan")
	categories = relationship("ScoreCategoryModel", back_populates="candidate_score", cascade="all, delete-orphan")
	insights = relationship("ScoreInsightModel", back_populates="candidate_score", cascade="all, delete-orphan")
	
	# Indexes
	__table_args__ = (
		Index('idx_candidate_persona', 'candidate_id', 'persona_id'),
		Index('idx_cv_persona', 'cv_id', 'persona_id'),
		Index('idx_scored_at', 'scored_at'),
	)


class ScoreStageModel(Base):
	"""Individual stage results within the scoring pipeline."""
	__tablename__ = "score_stages"

	id = Column(String, primary_key=True)
	candidate_score_id = Column(String, ForeignKey("candidate_scores.id", ondelete="CASCADE"), nullable=False, index=True)
	stage_number = Column(Integer, nullable=False)  # 1, 2, or 3
	
	# Stage-specific data
	method = Column(String, nullable=False)  # embedding_similarity, lightweight_llm, detailed_llm
	model = Column(String, nullable=True)  # gpt-4o-mini, etc.
	score = Column(DECIMAL(5, 2), nullable=False)
	threshold = Column(DECIMAL(5, 2), nullable=True)
	min_threshold = Column(DECIMAL(5, 2), nullable=True)
	decision = Column(String, nullable=False)  # PASS_TO_STAGE2, PASS_TO_STAGE3, REJECT
	reason = Column(Text, nullable=True)
	next_stage = Column(String, nullable=True)
	
	# Stage 2 specific fields
	relevance_score = Column(Integer, nullable=True)  # 0-100
	quick_assessment = Column(Text, nullable=True)
	
	# JSON fields for complex data
	skills_detected = Column(JSON, nullable=True)  # Array of skills
	roles_detected = Column(JSON, nullable=True)  # Array of roles
	key_matches = Column(JSON, nullable=True)  # Array of key matches
	key_gaps = Column(JSON, nullable=True)  # Array of gaps
	
	# Relationships
	candidate_score = relationship("CandidateScoreModel", back_populates="score_stages")
	
	# Indexes
	__table_args__ = (
		Index('idx_candidate_score_stage', 'candidate_score_id', 'stage_number'),
	)


class ScoreCategoryModel(Base):
	"""Category-level scoring results (e.g., Technical Skills, Cognitive Demands)."""
	__tablename__ = "score_categories"

	id = Column(String, primary_key=True)
	candidate_score_id = Column(String, ForeignKey("candidate_scores.id", ondelete="CASCADE"), nullable=False, index=True)
	category_name = Column(String, nullable=False)  # Technical Skills, Cognitive Demands, etc.
	weight_percentage = Column(Integer, nullable=False)  # 39, 14, 13, etc.
	category_score_percentage = Column(DECIMAL(5, 2), nullable=False)  # 45.75, 64.5, etc.
	category_contribution = Column(DECIMAL(5, 2), nullable=False)  # 17.84, 9.03, etc.
	
	# Relationships
	candidate_score = relationship("CandidateScoreModel", back_populates="categories")
	subcategories = relationship("ScoreSubcategoryModel", back_populates="category", cascade="all, delete-orphan")
	
	# Indexes
	__table_args__ = (
		Index('idx_candidate_score_category', 'candidate_score_id', 'category_name'),
	)


class ScoreSubcategoryModel(Base):
	"""Subcategory-level scoring results (e.g., Data Engineering Tools, Programming Languages)."""
	__tablename__ = "score_subcategories"

	id = Column(String, primary_key=True)
	category_id = Column(String, ForeignKey("score_categories.id", ondelete="CASCADE"), nullable=False, index=True)
	subcategory_name = Column(String, nullable=False)  # Data Engineering Tools, Programming Languages, etc.
	weight_percentage = Column(Integer, nullable=False)  # 35, 35, 20, etc.
	expected_level = Column(Integer, nullable=False)  # 5, 5, 4, etc.
	actual_level = Column(Integer, nullable=False)  # 3, 2, 3, etc.
	base_score = Column(DECIMAL(5, 2), nullable=False)  # 55, 50, 70, etc.
	missing_count = Column(Integer, nullable=False)  # 1, 2, 1, etc.
	scored_percentage = Column(DECIMAL(5, 2), nullable=False)  # 45, 30, 60, etc.
	notes = Column(Text, nullable=True)  # Detailed explanation
	
	# Relationships
	category = relationship("ScoreCategoryModel", back_populates="subcategories")
	
	# Indexes
	__table_args__ = (
		Index('idx_category_subcategory', 'category_id', 'subcategory_name'),
	)


class ScoreInsightModel(Base):
	"""Strengths and gaps identified during scoring."""
	__tablename__ = "score_insights"

	id = Column(String, primary_key=True)
	candidate_score_id = Column(String, ForeignKey("candidate_scores.id", ondelete="CASCADE"), nullable=False, index=True)
	insight_type = Column(String, nullable=False)  # STRENGTH, GAP
	insight_text = Column(Text, nullable=False)  # The actual strength/gap description
	
	# Relationships
	candidate_score = relationship("CandidateScoreModel", back_populates="insights")
	
	# Indexes
	__table_args__ = (
		Index('idx_candidate_score_type', 'candidate_score_id', 'insight_type'),
	)


# Legacy ScoreModel has been removed - use CandidateScoreModel and related models instead
