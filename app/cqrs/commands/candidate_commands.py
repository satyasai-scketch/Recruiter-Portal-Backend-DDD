# app/cqrs/commands/candidate_commands.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Command

@dataclass
class UpdateCandidate(Command):
    """Command to update a candidate."""
    def __init__(self, candidate_id: str, update_data: Dict[str, Any], user_id: Optional[str] = None):
        self.candidate_id = candidate_id
        self.update_data = update_data
        self.user_id = user_id

@dataclass
class UpdateCandidateCV(Command):
    """Command to update a candidate CV."""
    def __init__(self, cv_id: str, update_data: Dict[str, Any]):
        self.cv_id = cv_id
        self.update_data = update_data

@dataclass
class DeleteCandidate(Command):
    """Command to delete a candidate."""
    def __init__(self, candidate_id: str):
        self.candidate_id = candidate_id

@dataclass
class DeleteCandidateCV(Command):
    """Command to delete a candidate CV."""
    def __init__(self, candidate_cv_id: str):
        self.candidate_cv_id = candidate_cv_id
