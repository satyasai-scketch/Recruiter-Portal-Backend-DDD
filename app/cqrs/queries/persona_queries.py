# app/cqrs/queries/persona_queries.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Query

@dataclass
class GetPersona(Query):
    """Query to get a persona by ID."""
    def __init__(self, persona_id: str):
        self.persona_id = persona_id


@dataclass
class ListPersonasByJobDescription(Query):
    """Query to list personas by job description ID."""
    def __init__(self, job_description_id: str):
        self.job_description_id = job_description_id

@dataclass
class ListAllPersonas(Query):
    """Query to list all personas."""
    def __init__(self):
        pass

@dataclass
class CountPersonas(Query):
    """Query to count all personas."""
    def __init__(self):
        pass

@dataclass
class GetPersonaChangeLogs(Query):
    """Query to get change logs for a persona."""
    def __init__(self, persona_id: str):
        self.persona_id = persona_id

@dataclass
class ListPersonasByJobRole(Query):
    """Query to list personas by job role ID."""
    def __init__(self, role_id: str):
        self.role_id = role_id