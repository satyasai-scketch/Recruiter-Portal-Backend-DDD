# app/cqrs/queries/company_queries.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Query

@dataclass
class GetCompany(Query):
    """Query to get a company by ID."""
    def __init__(self, company_id: str):
        self.company_id = company_id

@dataclass
class GetCompanyByName(Query):
    """Query to get a company by name."""
    def __init__(self, name: str):
        self.name = name

@dataclass
class ListCompanies(Query):
    """Query to list companies with pagination."""
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit

@dataclass
class SearchCompanies(Query):
    """Query to search companies based on criteria."""
    def __init__(self, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100):
        self.search_criteria = search_criteria
        self.skip = skip
        self.limit = limit

@dataclass
class CountCompanies(Query):
    """Query to count total companies."""
    def __init__(self):
        pass

@dataclass
class CountSearchCompanies(Query):
    """Query to count companies matching search criteria."""
    def __init__(self, search_criteria: Dict[str, Any]):
        self.search_criteria = search_criteria
