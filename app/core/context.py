"""
Context variables for request-scoped data.
Used for LLM tracing and other cross-cutting concerns.
"""
from contextvars import ContextVar
from typing import Optional
from sqlalchemy.orm import Session

# Create context variables for request-scoped data
request_user_id: ContextVar[Optional[str]] = ContextVar('request_user_id', default=None)
request_db_session: ContextVar[Optional[Session]] = ContextVar('request_db_session', default=None)
request_action_type: ContextVar[Optional[str]] = ContextVar('request_action_type', default=None)

# Helper functions for easy access
def get_current_user_id() -> Optional[str]:
    """Get current user ID from context"""
    return request_user_id.get()

def get_current_db_session() -> Optional[Session]:
    """Get current DB session from context"""
    return request_db_session.get()

def get_current_action_type() -> Optional[str]:
    """Get current action type from context"""
    return request_action_type.get()

def set_request_context(user_id: Optional[str] = None, db_session: Optional[Session] = None, action_type: Optional[str] = None):
    """Helper to set multiple context variables at once"""
    if user_id is not None:
        request_user_id.set(user_id)
    if db_session is not None:
        request_db_session.set(db_session)
    if action_type is not None:
        request_action_type.set(action_type)

def clear_request_context():
    """Clear all context variables (useful for testing)"""
    # Note: ContextVar doesn't have a clear() method
    # We reset by creating a new context copy, but for practical purposes
    # we can just set them to None
    request_user_id.set(None)
    request_db_session.set(None)
    request_action_type.set(None)

