# Retrieval-augmented generation utilities (placeholders)

from typing import List, Protocol


class VectorIndex(Protocol):
	def search(self, query: str, top_k: int = 5) -> List[str]:
		...


def retrieve_best_practices(role: str) -> list[str]:
	return []
