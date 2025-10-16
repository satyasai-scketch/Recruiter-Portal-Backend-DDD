# Query classes for candidate operations

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
