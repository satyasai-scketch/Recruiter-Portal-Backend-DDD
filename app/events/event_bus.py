from typing import Callable, Dict, List


class EventBus:
	"""Very simple in-memory pub/sub (placeholder)."""

	def __init__(self):
		self._subscribers: Dict[str, List[Callable]] = {}

	def subscribe(self, event_name: str, handler: Callable) -> None:
		self._subscribers.setdefault(event_name, []).append(handler)

	def publish(self, event_name: str, payload: dict) -> None:
		for handler in self._subscribers.get(event_name, []):
			handler(payload)


event_bus = EventBus()
