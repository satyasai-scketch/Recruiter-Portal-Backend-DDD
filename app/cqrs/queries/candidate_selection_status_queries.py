# app/cqrs/queries/candidate_selection_status_queries.py
from dataclasses import dataclass
from typing import Optional
from .base import Query


@dataclass
class GetCandidateSelectionStatus(Query):
	"""Query to get a candidate selection status by ID."""
	def __init__(self, status_id: str):
		self.status_id = status_id


@dataclass
class GetCandidateSelectionStatusByCode(Query):
	"""Query to get a candidate selection status by code."""
	def __init__(self, code: str):
		self.code = code


@dataclass
class ListCandidateSelectionStatuses(Query):
	"""Query to list candidate selection statuses with pagination."""
	def __init__(self, skip: int = 0, limit: int = 100, active_only: bool = False):
		self.skip = skip
		self.limit = limit
		self.active_only = active_only


@dataclass
class ListActiveCandidateSelectionStatuses(Query):
	"""Query to list active candidate selection statuses ordered by display_order."""
	def __init__(self):
		pass


@dataclass
class CountCandidateSelectionStatuses(Query):
	"""Query to count total candidate selection statuses."""
	def __init__(self, active_only: bool = False):
		self.active_only = active_only

