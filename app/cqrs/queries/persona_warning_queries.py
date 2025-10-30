from dataclasses import dataclass
from .base import Query
from typing import Dict, Optional

@dataclass
class GetWarningByEntity(Query):
    """Query to fetch specific warning message"""
    persona_id: str
    entity_type: str
    entity_name: str
    violation_type: str  # "below_min" | "above_max"

@dataclass
class GetOrGenerateWarning(Query):
    """Query to get warning (generates if not exists)"""
    persona_id: Optional[str]
    entity_type: str
    entity_name: str
    violation_type: str
    entity_data: Optional[Dict] = None
@dataclass
class ListWarningsByPersona(Query):
    """Query to list all warnings for a persona"""
    persona_id: str