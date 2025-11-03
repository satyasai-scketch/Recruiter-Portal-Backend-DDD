"""
LLM Tracing context manager for tracking usage, costs, and latency.
"""
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.ai_tracing.action_types import ActionType, get_action_config
from app.db.models.llm_usage import LLMUsageModel
from app.repositories.llm_usage_repo import SQLAlchemyLLMUsageRepository
from app.core.logger import logger


class LLMTracingContext:
    """Context manager for tracking LLM usage"""
    
    def __init__(
        self,
        db: Session,
        action_type: ActionType,
        user_id: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "openai",
        context_data: Optional[Dict[str, Any]] = None
    ):
        self.db = db
        self.action_type = action_type
        self.user_id = user_id
        self.model = model
        self.provider = provider
        self.context_data = context_data
        
        self.start_time = None
        self.end_time = None
        self.input_tokens = 0
        self.output_tokens = 0
    
    async def __aenter__(self):
        self.start_time = datetime.now()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        
        # Calculate latency
        latency_ms = (self.end_time - self.start_time).total_seconds() * 1000
        
        # Only save if we have token information
        if self.input_tokens > 0 or self.output_tokens > 0:
            await self._save_usage(latency_ms)
        
        return False  # Don't suppress exceptions
    
    def record_tokens(self, input_tokens: int, output_tokens: int):
        """Record token usage from LLM response"""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
    
    async def _save_usage(self, latency_ms: float):
        """Save usage record to database"""
        try:
            from app.core.ai_pricing import calculate_cost
        except ImportError:
            # Fallback if ai_pricing.py doesn't exist yet
            from decimal import Decimal
            def calculate_cost(input_tokens: int, output_tokens: int, model: str):
                # Default to gpt-4o-mini pricing if module not found
                input_rate = Decimal('0.00015')
                output_rate = Decimal('0.0006')
                input_cost = (Decimal(input_tokens) / Decimal('1000')) * input_rate
                output_cost = (Decimal(output_tokens) / Decimal('1000')) * output_rate
                total_cost = input_cost + output_cost
                # Round to 7 decimal places
                SEVEN_PLACES = Decimal('0.0000001')
                return (
                    input_cost.quantize(SEVEN_PLACES),
                    output_cost.quantize(SEVEN_PLACES),
                    total_cost.quantize(SEVEN_PLACES)
                )
        
        config = get_action_config(self.action_type)
        model_name = self.model or "gpt-4o-mini"  # Use default fallback
        
        # Calculate costs using existing utility (returns Decimal values)
        input_cost_decimal, output_cost_decimal, total_cost_decimal = calculate_cost(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            model=model_name
        )
        
        # Convert Decimal to float for database storage
        usage_record = LLMUsageModel(
            id=str(uuid4()),
            action_type=self.action_type.value,
            action_parent=config.get("parent", "UNKNOWN"),
            action_name=config.get("action", "unknown"),
            user_id=self.user_id,
            provider=self.provider,
            model=model_name,
            start_time=self.start_time,
            end_time=self.end_time,
            latency_ms=latency_ms,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            total_tokens=self.input_tokens + self.output_tokens,
            input_cost_usd=float(input_cost_decimal),
            output_cost_usd=float(output_cost_decimal),
            total_cost_usd=float(total_cost_decimal),
            context_data=str(self.context_data) if self.context_data else None
        )
        
        # Use repository pattern instead of direct db operations
        repo = SQLAlchemyLLMUsageRepository()
        try:
            result = repo.create(self.db, usage_record)
            return result
        except Exception as e:
            logger.error(f"Failed to save LLM usage record: {type(e).__name__}: {e}", exc_info=True)
            # Repository handles rollback internally, but we re-raise for caller awareness
            raise

