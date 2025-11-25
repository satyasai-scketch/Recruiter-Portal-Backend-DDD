# Query classes for candidate operations

from typing import Optional, Dict, Any
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


class SearchCandidates(Query):
    """Query to search candidates based on criteria."""
    
    def __init__(self, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100):
        self.search_criteria = search_criteria
        self.skip = skip
        self.limit = limit


class CountSearchCandidates(Query):
    """Query to count candidates matching search criteria."""
    
    def __init__(self, search_criteria: Dict[str, Any]):
        self.search_criteria = search_criteria


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