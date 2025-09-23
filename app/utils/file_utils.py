from pathlib import Path


def save_upload(file_bytes: bytes, destination: Path) -> Path:
	"""Save uploaded file to destination (placeholder)."""
	destination.write_bytes(file_bytes)
	return destination
