from typing import Callable, Dict, List, Type, Any


class EventBus:
	"""Very simple in-memory pub/sub (placeholder)."""

	def __init__(self):
		self._subscribers: Dict[str, List[Callable]] = {}

	def subscribe(self, event_name: str, handler: Callable) -> None:
		self._subscribers.setdefault(event_name, []).append(handler)

	def subscribe_event(self, event_type: Type[Any], handler: Callable) -> None:
		self.subscribe(event_type.__name__, handler)

	def publish(self, event_name: str, payload: dict) -> None:
		for handler in self._subscribers.get(event_name, []):
			handler(payload)

	def publish_event(self, event_obj: Any) -> None:
		"""Publish an event object with error handling."""
		try:
			self.publish(event_obj.__class__.__name__, event_obj.__dict__)
		except Exception as e:
			# Log the error but don't raise it to avoid breaking the main operation
			print(f"EventBus: Failed to publish event {event_obj.__class__.__name__}: {e}")
			# Optionally, you could implement event retry logic or dead letter queue here


event_bus = EventBus()
