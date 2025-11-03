"""
Schemas for LLM Usage tracking.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LLMUsageBase(BaseModel):
    """Base schema for LLM usage"""
    action_type: str
    action_parent: str
    action_name: str
    user_id: Optional[str] = None
    provider: str
    model: str
    start_time: datetime
    end_time: datetime
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    context_data: Optional[str] = None


class LLMUsageCreate(LLMUsageBase):
    """Schema for creating LLM usage record"""
    pass


class LLMUsageRead(LLMUsageBase):
    """Schema for reading LLM usage record"""
    id: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LLMUsageSummary(BaseModel):
    """Summary statistics for LLM usage (user-specific)"""
    total_calls: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    by_action_type: dict[str, dict]  # Action type -> {count, tokens, cost_usd}


class LLMUsageTotalSummary(BaseModel):
    """Total usage statistics across all users"""
    total_calls: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    by_action_type: dict[str, dict]  # Action type -> {count, tokens, cost_usd}
    by_user: dict[str, dict]  # User ID -> {count, tokens, cost_usd}


class LLMUsageListResponse(BaseModel):
    """Paginated response for LLM usage records"""
    records: list[LLMUsageRead]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class LLMUsageFilter(BaseModel):
    """Filter parameters for querying LLM usage"""
    user_id: Optional[str] = None
    action_type: Optional[str] = None
    action_parent: Optional[str] = None
    model: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)

