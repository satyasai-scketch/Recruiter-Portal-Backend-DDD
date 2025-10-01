from dataclasses import dataclass


@dataclass
class JDCreatedEvent:
	id: str
	title: str
	role: str  # This can be role_id or role name depending on context
	company_id: str | None


@dataclass
class JDUpdatedEvent:
	id: str
	title: str
	role: str  # This can be role_id or role name depending on context


@dataclass
class JDFinalizedEvent:
	id: str
	selected_text: str
