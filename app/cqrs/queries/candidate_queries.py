# Query classes for candidate operations

from typing import Optional
from .base import Query


class GetCandidate(Query):
    """Query to get a candidate by ID."""
    
    def __init__(self, candidate_id: str):
        self.candidate_id = candidate_id


class ListAllCandidates(Query):
    """Query to list all candidates."""
    
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit


class GetCandidateCV(Query):
    """Query to get a candidate CV by ID."""
    
    def __init__(self, candidate_cv_id: str):
        self.candidate_cv_id = candidate_cv_id


class GetCandidateCVs(Query):
    """Query to get all CVs for a specific candidate."""
    
    def __init__(self, candidate_id: str):
        self.candidate_id = candidate_id


class ListSelectedCandidates(Query):
    """Query to list selected candidates with optional filtering."""
    
    def __init__(
        self,
        persona_id: Optional[str] = None,
        job_description_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ):
        self.persona_id = persona_id
        self.job_description_id = job_description_id
        self.status = status
        self.skip = skip
        self.limit = limit


class GetCandidateSelection(Query):
    """Query to get a candidate selection by ID."""
    
    def __init__(self, selection_id: str):
        self.selection_id = selection_id