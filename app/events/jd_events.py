from dataclasses import dataclass


@dataclass
class JDCreatedEvent:
	id: str
	title: str
	role: str
	company_id: str | None


@dataclass
class JDFinalizedEvent:
	id: str
	selected_text: str
