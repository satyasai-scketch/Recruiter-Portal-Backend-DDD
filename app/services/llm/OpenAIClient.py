from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from .base import LLMChatClient
from langsmith.wrappers import wrap_openai
from app.services.ai_tracing.tracing import LLMTracingContext
from app.services.ai_tracing.action_types import ActionType
from app.core.context import get_current_user_id, get_current_db_session, get_current_action_type
from app.core.logger import logger

class OpenAIClient(LLMChatClient):
    """OpenAI chat client with automatic context-based tracing"""
    
    def __init__(self, api_key: str, action_type: Optional[ActionType] = None):
        self.client = wrap_openai(AsyncOpenAI(api_key=api_key))
        self.action_type = action_type  # Can be set explicitly or retrieved from context
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, Any]],
        model: str = "gpt-4o-mini", 
        temperature: float = 0.7, 
        max_tokens: int = 5000,
        response_format: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate a chat completion with automatic tracing from context"""
        
        # Get context variables (automatically available in async context)
        db = get_current_db_session()
        user_id = get_current_user_id()
        
        # Prefer explicit action_type over context (explicit is more accurate)
        action_type = self.action_type
        if action_type is None:
            # Fallback to context if no explicit type set
            action_type_str = get_current_action_type()
            if action_type_str:
                try:
                    action_type = ActionType(action_type_str)
                except (ValueError, TypeError):
                    action_type = None
        
        # If tracing is enabled (context variables available)
        if db and action_type:
            async with LLMTracingContext(
                db=db,
                action_type=action_type,
                user_id=user_id,
                model=model,
                provider="openai"
            ) as tracing:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format
                )
                
                # Extract token usage
                if hasattr(response, 'usage') and response.usage:
                    tokens_in = getattr(response.usage, 'prompt_tokens', 0) or 0
                    tokens_out = getattr(response.usage, 'completion_tokens', 0) or 0
                    tracing.record_tokens(
                        input_tokens=tokens_in,
                        output_tokens=tokens_out
                    )
                
                return response
        else:
            # Original behavior - no tracing (backward compatible)
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            return response

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': 'openai',
            'model': getattr(self, '_last_model', None),
        }
