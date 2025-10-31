"""
Action types for LLM usage tracking with hierarchical parent-child relationship.
Based on actual chat_completion usage across the codebase.
"""
from enum import Enum
from typing import Dict, Any

class ActionType(str, Enum):
    """Action types for LLM operations"""
    
    # JD Operations
    JD_REFINE = "JD_REFINE"
    JD_IMPROVEMENT = "JD_IMPROVEMENT"
    JD_ANALYZE = "JD_ANALYZE"
    JD_TEMPLATE = "JD_TEMPLATE"
    
    # PERSONA Operations
    PERSONA_GEN = "PERSONA_GEN"
    PERSONA_ANALYZE = "PERSONA_ANALYZE"
    PERSONA_VALIDATE = "PERSONA_VALIDATE"
    PERSONA_WEIGHT = "PERSONA_WEIGHT"
    
    # CV Operations
    CV_SCORE = "CV_SCORE"
    CV_SCREEN = "CV_SCREEN"
    CV_MATCH = "CV_MATCH"
    CV_EXTRACT = "CV_EXTRACT"
    CV_EMBED = "CV_EMBED"

ACTION_TYPE_CONFIG: Dict[ActionType, Dict[str, Any]] = {
    # JD Operations
    ActionType.JD_REFINE: {
        "parent": "JD",
        "action": "jd_refinement",
        "description": "Refine job descriptions using AI (includes refinement and improvement extraction)"
    },
    ActionType.JD_IMPROVEMENT: {
        "parent": "JD",
        "action": "jd_improvement",
        "description": "Extract improvements from JD refinement"
    },
    ActionType.JD_ANALYZE: {
        "parent": "JD",
        "action": "jd_analysis",
        "description": "Analyze JD structure and requirements"
    },
    ActionType.JD_TEMPLATE: {
        "parent": "JD",
        "action": "jd_template",
        "description": "Generate JD templates using AI"
    },
    
    # PERSONA Operations
    ActionType.PERSONA_GEN: {
        "parent": "PERSONA",
        "action": "persona_generation",
        "description": "Generate complete persona structure from JD (includes structure building)"
    },
    ActionType.PERSONA_ANALYZE: {
        "parent": "PERSONA",
        "action": "persona_analysis",
        "description": "Analyze JD for persona creation (deep JD analysis phase)"
    },
    ActionType.PERSONA_VALIDATE: {
        "parent": "PERSONA",
        "action": "persona_validation",
        "description": "Validate and correct persona structure (self-validation phase)"
    },
    ActionType.PERSONA_WEIGHT: {
        "parent": "PERSONA",
        "action": "persona_weighting",
        "description": "Generate persona warning messages for weight violations"
    },
    
    # CV Operations
    ActionType.CV_SCORE: {
        "parent": "CV",
        "action": "cv_scoring",
        "description": "Comprehensive CV scoring (includes category scoring and summary generation)"
    },
    ActionType.CV_SCREEN: {
        "parent": "CV",
        "action": "cv_screening",
        "description": "Lightweight CV screening with skill extraction and role detection"
    },
    ActionType.CV_MATCH: {
        "parent": "CV",
        "action": "cv_matching",
        "description": "Semantic CV matching using embeddings"
    },
    ActionType.CV_EXTRACT: {
        "parent": "CV",
        "action": "cv_extraction",
        "description": "Extract structured data from CVs using AI"
    },
    ActionType.CV_EMBED: {
        "parent": "CV",
        "action": "cv_embedding",
        "description": "Generate CV embeddings for semantic search"
    }
}

def get_action_config(action_type: ActionType) -> Dict[str, Any]:
    """Get configuration for an action type"""
    return ACTION_TYPE_CONFIG.get(action_type, {
        "parent": "UNKNOWN",
        "action": "unknown",
        "description": "Unknown action"
    })

