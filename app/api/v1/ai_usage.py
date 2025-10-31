"""
API endpoints for AI Usage tracking.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import db_session, get_current_user
from app.db.models.user import UserModel
from app.db.models.llm_usage import LLMUsageModel
from app.repositories.llm_usage_repo import SQLAlchemyLLMUsageRepository
from app.schemas.llm_usage import (
    LLMUsageRead,
    LLMUsageSummary,
    LLMUsageTotalSummary,
    LLMUsageListResponse
)


router = APIRouter()


def _convert_usage_model_to_read_schema(usage_model: LLMUsageModel) -> LLMUsageRead:
    """Convert LLMUsageModel to LLMUsageRead schema."""
    return LLMUsageRead.model_validate(usage_model)


def _get_total_count(
    db: Session,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    action_parent: Optional[str] = None,
    model: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> int:
    """Get total count of records matching the filters."""
    query = db.query(func.count(LLMUsageModel.id))
    
    if user_id:
        query = query.filter(LLMUsageModel.user_id == user_id)
    if action_type:
        query = query.filter(LLMUsageModel.action_type == action_type)
    if action_parent:
        query = query.filter(LLMUsageModel.action_parent == action_parent)
    if model:
        query = query.filter(LLMUsageModel.model == model)
    if start_date:
        query = query.filter(LLMUsageModel.created_at >= start_date)
    if end_date:
        query = query.filter(LLMUsageModel.created_at <= end_date)
    
    return query.scalar() or 0


@router.get(
    "/",
    response_model=LLMUsageListResponse,
    summary="List AI usage records with filters"
)
async def list_ai_usage(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type (e.g., JD_REFINE, CV_SCORE)"),
    action_parent: Optional[str] = Query(None, description="Filter by action parent (JD, PERSONA, CV)"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List AI usage records with optional filters and pagination.
    
    - **page**: Page number (starts at 1)
    - **size**: Number of records per page (max 100)
    - **user_id**: Filter by specific user ID
    - **action_type**: Filter by action type (e.g., JD_REFINE, PERSONA_GEN, CV_SCORE)
    - **action_parent**: Filter by parent category (JD, PERSONA, CV)
    - **model**: Filter by model name (e.g., gpt-4o, gpt-4o-mini)
    - **start_date**: Filter records from this date (ISO format)
    - **end_date**: Filter records until this date (ISO format)
    """
    repo = SQLAlchemyLLMUsageRepository()
    skip = (page - 1) * size
    
    # Get records with filters
    records = repo.list_with_filters(
        db=db,
        user_id=user_id,
        action_type=action_type,
        action_parent=action_parent,
        model=model,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=size
    )
    
    # Get total count
    total = _get_total_count(
        db=db,
        user_id=user_id,
        action_type=action_type,
        action_parent=action_parent,
        model=model,
        start_date=start_date,
        end_date=end_date
    )
    
    # Convert to response format
    record_reads = [_convert_usage_model_to_read_schema(record) for record in records]
    
    return LLMUsageListResponse(
        records=record_reads,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
        has_prev=page > 1
    )


@router.get(
    "/{usage_id}",
    response_model=LLMUsageRead,
    summary="Get AI usage record by ID"
)
async def get_ai_usage(
    usage_id: str,
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a specific AI usage record by its ID.
    """
    repo = SQLAlchemyLLMUsageRepository()
    record = repo.get_by_id(db, usage_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Usage record not found")
    
    return _convert_usage_model_to_read_schema(record)


@router.get(
    "/user/{user_id}",
    response_model=LLMUsageListResponse,
    summary="Get AI usage records for a specific user"
)
async def get_user_ai_usage(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all AI usage records for a specific user with pagination.
    """
    repo = SQLAlchemyLLMUsageRepository()
    skip = (page - 1) * size
    
    # Get records for user
    records = repo.list_by_user(db, user_id, skip=skip, limit=size)
    
    # Get total count for user
    total = _get_total_count(db, user_id=user_id)
    
    # Convert to response format
    record_reads = [_convert_usage_model_to_read_schema(record) for record in records]
    
    return LLMUsageListResponse(
        records=record_reads,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
        has_prev=page > 1
    )


@router.get(
    "/user/{user_id}/summary",
    response_model=LLMUsageSummary,
    summary="Get AI usage summary for a specific user"
)
async def get_user_ai_usage_summary(
    user_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get aggregated usage statistics for a specific user.
    
    Returns:
    - Total number of API calls
    - Total tokens used
    - Total cost in USD
    - Average latency in milliseconds
    - Breakdown by action type
    """
    repo = SQLAlchemyLLMUsageRepository()
    summary = repo.get_user_summary(db, user_id, start_date, end_date)
    return LLMUsageSummary(**summary)


@router.get(
    "/action-type/{action_type}",
    response_model=LLMUsageListResponse,
    summary="Get AI usage records by action type"
)
async def get_ai_usage_by_action_type(
    action_type: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all AI usage records for a specific action type.
    
    Action types include: JD_REFINE, JD_ANALYZE, PERSONA_GEN, PERSONA_ANALYZE,
    CV_SCORE, CV_SCREEN, etc.
    """
    repo = SQLAlchemyLLMUsageRepository()
    skip = (page - 1) * size
    
    # Get records by action type
    records = repo.list_by_action_type(db, action_type, skip=skip, limit=size)
    
    # Get total count
    total = _get_total_count(db, action_type=action_type)
    
    # Convert to response format
    record_reads = [_convert_usage_model_to_read_schema(record) for record in records]
    
    return LLMUsageListResponse(
        records=record_reads,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
        has_prev=page > 1
    )


@router.get(
    "/action-parent/{action_parent}",
    response_model=LLMUsageListResponse,
    summary="Get AI usage records by action parent category"
)
async def get_ai_usage_by_action_parent(
    action_parent: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all AI usage records for a specific action parent category.
    
    Action parents include: JD, PERSONA, CV
    """
    repo = SQLAlchemyLLMUsageRepository()
    skip = (page - 1) * size
    
    # Get records by action parent
    records = repo.list_by_action_parent(db, action_parent, skip=skip, limit=size)
    
    # Get total count
    total = _get_total_count(db, action_parent=action_parent)
    
    # Convert to response format
    record_reads = [_convert_usage_model_to_read_schema(record) for record in records]
    
    return LLMUsageListResponse(
        records=record_reads,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
        has_prev=page > 1
    )


@router.get(
    "/summary/total",
    response_model=LLMUsageTotalSummary,
    summary="Get total AI usage summary across all users"
)
async def get_total_ai_usage_summary(
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get aggregated usage statistics across all users.
    
    Returns:
    - Total number of API calls
    - Total tokens used
    - Total cost in USD
    - Average latency in milliseconds
    - Breakdown by action type
    - Breakdown by user
    """
    repo = SQLAlchemyLLMUsageRepository()
    summary = repo.get_total_usage(db, start_date, end_date)
    return LLMUsageTotalSummary(**summary)


@router.get(
    "/summary/my-usage",
    response_model=LLMUsageSummary,
    summary="Get AI usage summary for current authenticated user"
)
async def get_my_ai_usage_summary(
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get aggregated usage statistics for the currently authenticated user.
    """
    repo = SQLAlchemyLLMUsageRepository()
    summary = repo.get_user_summary(db, current_user.id, start_date, end_date)
    return LLMUsageSummary(**summary)

