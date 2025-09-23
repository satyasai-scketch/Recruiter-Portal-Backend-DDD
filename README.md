# Recruiter AI Backend

FastAPI backend implementing DDD + CQRS + Events architecture for a recruiter application that matches CVs to job descriptions with AI-assisted workflows.

- Tech: FastAPI, SQLAlchemy, Pydantic, Alembic
- Patterns: Domain-Driven Design, CQRS, Event-driven

## Quick start

1. Create and populate `.env` from `.env.example`.
2. Install deps: `pip install -r requirements.txt`.
3. Run dev server: `uvicorn app.main:app --reload`.

## Structure

See the `app/` tree for the layered structure.
