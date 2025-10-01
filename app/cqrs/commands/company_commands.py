# app/cqrs/commands/company_commands.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Command

@dataclass
class CreateCompany(Command):
    """Command to create a new company."""
    def __init__(self, payload: dict):
        self.payload = payload

@dataclass
class UpdateCompany(Command):
    """Command to update an existing company."""
    def __init__(self, company_id: str, payload: dict):
        self.company_id = company_id
        self.payload = payload

@dataclass
class DeleteCompany(Command):
    """Command to delete a company."""
    def __init__(self, company_id: str):
        self.company_id = company_id
