# Simple CQRS dispatcher stubs

class Command:  # placeholder
	pass


class Query:  # placeholder
	pass


def handle_command(command: Command) -> dict:
	return {"message": "stub: command handled"}


def handle_query(query: Query) -> dict:
	return {"message": "stub: query handled"}
