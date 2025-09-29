# app/cqrs/commands/job_role_commands.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Command

@dataclass
class CreateJobRole(Command):
    """Command to create a new job role."""
    def __init__(self, payload: dict):
        self.payload = payload

@dataclass
class UpdateJobRole(Command):
    """Command to update an existing job role."""
    def __init__(self, job_role_id: str, payload: dict):
        self.job_role_id = job_role_id
        self.payload = payload

@dataclass
class DeleteJobRole(Command):
    """Command to delete a job role."""
    def __init__(self, job_role_id: str):
        self.job_role_id = job_role_id
