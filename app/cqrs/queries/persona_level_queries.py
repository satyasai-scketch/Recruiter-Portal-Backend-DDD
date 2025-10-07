# app/cqrs/queries/persona_level_queries.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Query

@dataclass
class GetPersonaLevel(Query):
    """Query to get a persona level by ID."""
    def __init__(self, persona_level_id: str):
        self.persona_level_id = persona_level_id

@dataclass
class GetPersonaLevelByName(Query):
    """Query to get a persona level by name."""
    def __init__(self, name: str):
        self.name = name

@dataclass
class GetPersonaLevelByPosition(Query):
    """Query to get a persona level by position."""
    def __init__(self, position: int):
        self.position = position
        
@dataclass
class ListPersonaLevels(Query):
    """Query to list persona levels with sort_by_position option."""
    def __init__(self, sort_by_position: bool = True):
        self.sort_by_position = sort_by_position

@dataclass
class ListAllPersonaLevels(Query):
    """Query to list all persona levels."""
    def __init__(self):
        pass