# app/cqrs/commands/candidate_commands.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Command

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
