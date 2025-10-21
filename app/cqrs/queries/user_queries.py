from __future__ import annotations

from app.cqrs.queries.base import Query


class ListAllUsers(Query):
	"""Query to list all users."""
	
	def __init__(self, skip: int = 0, limit: int = 100):
		self.skip = skip
		self.limit = limit


class GetUser(Query):
	"""Query to get a user by ID."""
	
	def __init__(self, user_id: str):
		self.user_id = user_id
