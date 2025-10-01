from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass(frozen=True)
class JobRole:
	"""Value object representing the job role or title keyword.

	Immutable and validated at creation time via rules layer in application flow.
	"""

	name: str

	def __post_init__(self) -> None:
		if not self.name or not self.name.strip():
			raise ValueError("JobRole.name must be a non-empty string")


@dataclass(frozen=True)
class CompanyProfileRef:
	"""Lightweight reference to a company profile in the domain.

	This is a value object carrying the identifier only. No persistence concerns.
	"""

	company_id: str

	def __post_init__(self) -> None:
		if not self.company_id or not self.company_id.strip():
			raise ValueError("CompanyProfileRef.company_id must be a non-empty string")


@dataclass(frozen=True)
class RefinementNotes:
	"""Optional recruiter-provided notes to influence refinement."""

	text: str

	def __post_init__(self) -> None:
		# Allow empty string but ensure it's a string type
		if self.text is None:
			raise ValueError("RefinementNotes.text cannot be None")


@dataclass(frozen=True)
class DocumentMetadata:
	"""Metadata about the original document uploaded."""
	
	filename: str
	file_size: int
	file_extension: str
	word_count: int
	character_count: int
	
	def __post_init__(self) -> None:
		if not self.filename or not self.filename.strip():
			raise ValueError("DocumentMetadata.filename must be a non-empty string")
		if self.file_size < 0:
			raise ValueError("DocumentMetadata.file_size must be non-negative")
		if not self.file_extension or not self.file_extension.strip():
			raise ValueError("DocumentMetadata.file_extension must be a non-empty string")
		if self.word_count < 0:
			raise ValueError("DocumentMetadata.word_count must be non-negative")
		if self.character_count < 0:
			raise ValueError("DocumentMetadata.character_count must be non-negative")


@dataclass
class JobDescription:
	"""Aggregate root for a Job Description within the domain.

	The aggregate holds both the original and refined variants. Refinement is a
	pure-domain operation (see services) that produces a new `refined_text`.
	"""

	id: Optional[str]
	title: str
	role: JobRole
	original_text: str
	refined_text: Optional[str] = None
	company: Optional[CompanyProfileRef] = None
	notes: Optional[RefinementNotes] = None
	tags: List[str] = field(default_factory=list)
	document_metadata: Optional[DocumentMetadata] = None

	def has_refined(self) -> bool:
		"""Return True if a refined version currently exists on this aggregate."""
		return bool(self.refined_text and self.refined_text.strip())

	def select_final_text(self, use_refined: bool) -> str:
		"""Return the selected text variant for downstream processes.

		This method does not mutate; selection is an ephemeral decision for the
		application layer. Persisting a selection is outside the domain aggregate.
		"""
		if use_refined and self.has_refined():
			return self.refined_text or self.original_text
		return self.original_text
