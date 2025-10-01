# app/events/job_role_events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class JobRoleCreatedEvent:
    """Event published when a job role is created."""
    job_role_id: str
    job_role_name: str
    created_by: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class JobRoleUpdatedEvent:
    """Event published when a job role is updated."""
    job_role_id: str
    job_role_name: str
    updated_by: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class JobRoleDeletedEvent:
    """Event published when a job role is deleted."""
    job_role_id: str
    job_role_name: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
