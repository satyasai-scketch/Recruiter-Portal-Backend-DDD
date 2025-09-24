from typing import Dict

from app.events.event_bus import event_bus
from app.events.jd_events import JDFinalizedEvent, JDCreatedEvent
from app.events.persona_events import PersonaCreatedEvent
from app.events.candidate_events import CVUploadedEvent, ScoreRequestedEvent
from app.workers.cv_batch_worker import run_cv_batch_job
from app.workers.scorer_worker import run_scorer_job


def handle_jd_finalized(payload: Dict) -> None:
	_ = payload  # In real system, enqueue a job; here we no-op


def handle_jd_created(payload: Dict) -> None:
	_ = payload


def handle_persona_created(payload: Dict) -> None:
	_ = payload


def handle_cv_uploaded(payload: Dict) -> None:
	# Run a batch CV processing job (stub)
	candidate_ids = payload.get("candidate_ids", [])
	if candidate_ids:
		run_cv_batch_job(job_id="cv_batch:" + ",".join(candidate_ids))


def handle_score_requested(payload: Dict) -> None:
	# Run a scoring job (stub)
	run_scorer_job(job_id=f"score:{payload.get('persona_id', '')}")


def register_event_handlers() -> None:
	event_bus.subscribe_event(JDFinalizedEvent, handle_jd_finalized)
	event_bus.subscribe_event(JDCreatedEvent, handle_jd_created)
	event_bus.subscribe_event(PersonaCreatedEvent, handle_persona_created)
	event_bus.subscribe_event(CVUploadedEvent, handle_cv_uploaded)
	event_bus.subscribe_event(ScoreRequestedEvent, handle_score_requested)
