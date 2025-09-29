# app/cqrs/queries/job_role_queries.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Query

@dataclass
class GetJobRole(Query):
    """Query to get a job role by ID."""
    def __init__(self, job_role_id: str):
        self.job_role_id = job_role_id

@dataclass
class GetJobRoleByName(Query):
    """Query to get a job role by name."""
    def __init__(self, name: str):
        self.name = name

@dataclass
class ListJobRoles(Query):
    """Query to list job roles with pagination."""
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit

@dataclass
class ListActiveJobRoles(Query):
    """Query to list active job roles with pagination."""
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit

@dataclass
class GetJobRolesByCategory(Query):
    """Query to get job roles by category."""
    def __init__(self, category: str, skip: int = 0, limit: int = 100):
        self.category = category
        self.skip = skip
        self.limit = limit

@dataclass
class SearchJobRoles(Query):
    """Query to search job roles based on criteria."""
    def __init__(self, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100):
        self.search_criteria = search_criteria
        self.skip = skip
        self.limit = limit

@dataclass
class CountJobRoles(Query):
    """Query to count total job roles."""
    def __init__(self):
        pass

@dataclass
class CountActiveJobRoles(Query):
    """Query to count active job roles."""
    def __init__(self):
        pass

@dataclass
class CountSearchJobRoles(Query):
    """Query to count job roles matching search criteria."""
    def __init__(self, search_criteria: Dict[str, Any]):
        self.search_criteria = search_criteria

@dataclass
class GetJobRoleCategories(Query):
    """Query to get all unique job role categories."""
    def __init__(self):
        pass
