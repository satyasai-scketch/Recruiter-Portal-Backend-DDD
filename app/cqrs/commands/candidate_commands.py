# app/cqrs/commands/candidate_commands.py
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
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

@dataclass
class SelectCandidates(Command):
    """Command to select multiple candidates for interview."""
    def __init__(
        self,
        candidate_ids: List[str],
        persona_id: str,
        job_description_id: str,
        selected_by: str,
        selection_notes: Optional[str] = None,
        priority: Optional[str] = None
    ):
        self.candidate_ids = candidate_ids
        self.persona_id = persona_id
        self.job_description_id = job_description_id
        self.selected_by = selected_by
        self.selection_notes = selection_notes
        self.priority = priority

@dataclass
class UpdateCandidateSelection(Command):
    """Command to update a candidate selection."""
    def __init__(
        self,
        selection_id: str,
        updated_by: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        selection_notes: Optional[str] = None,
        change_notes: Optional[str] = None
    ):
        self.selection_id = selection_id
        self.updated_by = updated_by
        self.status = status
        self.priority = priority
        self.selection_notes = selection_notes
        self.change_notes = change_notes