"""
Repository for LLM Usage tracking.
"""
from __future__ import annotations

from typing import Optional, List, Sequence
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.db.models.llm_usage import LLMUsageModel


class LLMUsageRepository:
    """Repository interface for LLM usage records."""

    def create(self, db: Session, usage_record: LLMUsageModel) -> LLMUsageModel:
        """Create a new LLM usage record."""
        raise NotImplementedError

    def get_by_id(self, db: Session, usage_id: str) -> Optional[LLMUsageModel]:
        """Get usage record by ID."""
        raise NotImplementedError

    def list_by_user(
        self, 
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records for a specific user."""
        raise NotImplementedError

    def list_by_action_type(
        self, 
        db: Session, 
        action_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records by action type."""
        raise NotImplementedError

    def list_by_action_parent(
        self, 
        db: Session, 
        action_parent: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records by action parent (JD, PERSONA, CV)."""
        raise NotImplementedError

    def list_with_filters(
        self,
        db: Session,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        action_parent: Optional[str] = None,
        model: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records with multiple filters."""
        raise NotImplementedError

    def get_user_summary(
        self,
        db: Session,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get summary statistics for a user."""
        raise NotImplementedError

    def get_total_usage(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get total usage statistics across all users."""
        raise NotImplementedError


class SQLAlchemyLLMUsageRepository(LLMUsageRepository):
    """SQLAlchemy-backed implementation of LLMUsageRepository."""

    def create(self, db: Session, usage_record: LLMUsageModel) -> LLMUsageModel:
        """Create a new LLM usage record."""
        try:
            db.add(usage_record)
            db.commit()
            db.refresh(usage_record)
            return usage_record
        except Exception as e:
            db.rollback()
            raise e

    def get_by_id(self, db: Session, usage_id: str) -> Optional[LLMUsageModel]:
        """Get usage record by ID."""
        return db.query(LLMUsageModel).filter(LLMUsageModel.id == usage_id).first()

    def list_by_user(
        self, 
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records for a specific user."""
        return (
            db.query(LLMUsageModel)
            .filter(LLMUsageModel.user_id == user_id)
            .order_by(desc(LLMUsageModel.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_action_type(
        self, 
        db: Session, 
        action_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records by action type."""
        return (
            db.query(LLMUsageModel)
            .filter(LLMUsageModel.action_type == action_type)
            .order_by(desc(LLMUsageModel.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_action_parent(
        self, 
        db: Session, 
        action_parent: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records by action parent (JD, PERSONA, CV)."""
        return (
            db.query(LLMUsageModel)
            .filter(LLMUsageModel.action_parent == action_parent)
            .order_by(desc(LLMUsageModel.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_with_filters(
        self,
        db: Session,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        action_parent: Optional[str] = None,
        model: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[LLMUsageModel]:
        """List usage records with multiple filters."""
        query = db.query(LLMUsageModel)
        
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
        
        return (
            query
            .order_by(desc(LLMUsageModel.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_summary(
        self,
        db: Session,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get summary statistics for a user."""
        query = db.query(LLMUsageModel).filter(LLMUsageModel.user_id == user_id)
        
        if start_date:
            query = query.filter(LLMUsageModel.created_at >= start_date)
        if end_date:
            query = query.filter(LLMUsageModel.created_at <= end_date)
        
        results = query.all()
        
        if not results:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_latency_ms": 0.0,
                "by_action_type": {}
            }
        
        total_calls = len(results)
        total_tokens = sum(r.total_tokens for r in results)
        total_cost_usd = sum(r.total_cost_usd for r in results)
        avg_latency_ms = sum(r.latency_ms for r in results) / total_calls if total_calls > 0 else 0.0
        
        # Group by action type
        by_action_type = {}
        for record in results:
            action_type = record.action_type
            if action_type not in by_action_type:
                by_action_type[action_type] = {
                    "count": 0,
                    "tokens": 0,
                    "cost_usd": 0.0
                }
            by_action_type[action_type]["count"] += 1
            by_action_type[action_type]["tokens"] += record.total_tokens
            by_action_type[action_type]["cost_usd"] += record.total_cost_usd
        
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 6),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "by_action_type": by_action_type
        }

    def get_total_usage(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get total usage statistics across all users."""
        query = db.query(LLMUsageModel)
        
        if start_date:
            query = query.filter(LLMUsageModel.created_at >= start_date)
        if end_date:
            query = query.filter(LLMUsageModel.created_at <= end_date)
        
        results = query.all()
        
        if not results:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_latency_ms": 0.0,
                "by_action_type": {},
                "by_user": {}
            }
        
        total_calls = len(results)
        total_tokens = sum(r.total_tokens for r in results)
        total_cost_usd = sum(r.total_cost_usd for r in results)
        avg_latency_ms = sum(r.latency_ms for r in results) / total_calls if total_calls > 0 else 0.0
        
        # Group by action type
        by_action_type = {}
        for record in results:
            action_type = record.action_type
            if action_type not in by_action_type:
                by_action_type[action_type] = {
                    "count": 0,
                    "tokens": 0,
                    "cost_usd": 0.0
                }
            by_action_type[action_type]["count"] += 1
            by_action_type[action_type]["tokens"] += record.total_tokens
            by_action_type[action_type]["cost_usd"] += record.total_cost_usd
        
        # Group by user
        by_user = {}
        for record in results:
            user_id = record.user_id or "anonymous"
            if user_id not in by_user:
                by_user[user_id] = {
                    "count": 0,
                    "tokens": 0,
                    "cost_usd": 0.0
                }
            by_user[user_id]["count"] += 1
            by_user[user_id]["tokens"] += record.total_tokens
            by_user[user_id]["cost_usd"] += record.total_cost_usd
        
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 6),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "by_action_type": by_action_type,
            "by_user": by_user
        }

