from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime


class ScorePayload(BaseModel):
	"""Request payload for comprehensive candidate scoring"""
	candidate_id: str
	persona_id: str
	cv_id: str
	ai_scoring_response: Dict[str, Any]
	scoring_version: str = "v1.0"
	processing_time_ms: Optional[int] = None


class ScoreStageRead(BaseModel):
	"""Schema for individual stage results"""
	id: str
	candidate_score_id: str
	stage_number: int
	method: str
	model: Optional[str] = None
	score: float
	threshold: Optional[float] = None
	min_threshold: Optional[float] = None
	decision: str
	reason: Optional[str] = None
	next_stage: Optional[str] = None
	relevance_score: Optional[float] = None
	quick_assessment: Optional[str] = None
	skills_detected: Optional[List[str]] = None
	roles_detected: Optional[List[str]] = None
	key_matches: Optional[List[str]] = None
	key_gaps: Optional[List[str]] = None


class ScoreSubcategoryRead(BaseModel):
	"""Schema for subcategory scoring results"""
	id: str
	category_id: str
	subcategory_name: str
	weight_percentage: int
	expected_level: int
	actual_level: int
	base_score: float
	missing_count: int
	scored_percentage: float
	notes: Optional[str] = None


class ScoreCategoryRead(BaseModel):
	"""Schema for category scoring results"""
	id: str
	candidate_score_id: str
	category_name: str
	weight_percentage: int
	category_score_percentage: float
	category_contribution: float
	subcategories: List[ScoreSubcategoryRead] = []


class ScoreInsightRead(BaseModel):
	"""Schema for strengths and gaps"""
	id: str
	candidate_score_id: str
	insight_type: str  # STRENGTH or GAP
	insight_text: str


class CandidateScoreRead(BaseModel):
	"""Schema for comprehensive candidate scoring results"""
	id: str
	candidate_id: str
	persona_id: str
	cv_id: str
	pipeline_stage_reached: int
	final_score: float
	final_decision: str
	embedding_score: Optional[float] = None
	lightweight_llm_score: Optional[float] = None
	detailed_llm_score: Optional[float] = None
	scored_at: datetime
	scoring_version: Optional[str] = None
	processing_time_ms: Optional[int] = None
	candidate_name: Optional[str] = None
	file_name: Optional[str] = None
	persona_name: Optional[str] = None
	role_name: Optional[str] = None
	is_selected: int = 0  # 1 if candidate is selected for this persona, 0 otherwise
	
	# Related data
	score_stages: List[ScoreStageRead] = []
	categories: List[ScoreCategoryRead] = []
	insights: List[ScoreInsightRead] = []


class ScoreResponse(BaseModel):
	"""Response for scoring endpoint"""
	score_id: str
	candidate_id: str
	persona_id: str
	final_score: float
	final_decision: str
	pipeline_stage_reached: int
	scored_at: datetime
	candidate_name: Optional[str] = None
	file_name: Optional[str] = None
	persona_name: Optional[str] = None
	role_name: Optional[str] = None
	is_selected: int = 0  # 1 if candidate is selected for this persona, 0 otherwise


class ScoreListResponse(BaseModel):
	"""Response for listing scores"""
	scores: List[CandidateScoreRead]
	total: int
	page: int
	size: int
	has_next: bool
	has_prev: bool
