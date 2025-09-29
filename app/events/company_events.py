# app/events/company_events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CompanyCreatedEvent:
    """Event published when a company is created."""
    company_id: str
    company_name: str
    created_by: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class CompanyUpdatedEvent:
    """Event published when a company is updated."""
    company_id: str
    company_name: str
    updated_by: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class CompanyDeletedEvent:
    """Event published when a company is deleted."""
    company_id: str
    company_name: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
