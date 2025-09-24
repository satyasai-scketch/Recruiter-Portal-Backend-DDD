# Embeddings utilities (placeholders)

from typing import Protocol, List


class EmbeddingsClient(Protocol):
	def embed(self, texts: List[str]) -> List[List[float]]:
		...


def embed_text(text: str) -> list[float]:
	return [0.0]
