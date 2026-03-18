import logging
import uuid
from datetime import datetime, timezone

from sqlmodel import Session, create_engine

from app.core.config import settings
from app.db.models import Evaluation, EvaluationResult, TaskStatus
from app.scheduler.celery_app import celery_app

logger = logging.getLogger(__name__)

# Celery tasks use sync DB access
_sync_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)


def _get_sync_session() -> Session:
    return Session(_sync_engine)


@celery_app.task(bind=True, name="run_evaluation")
def run_evaluation(self, evaluation_id: str) -> dict:
    """Execute a model evaluation via EvalScope.

    This task runs synchronously inside a Celery worker. It updates the
    evaluation status in the database as it progresses.
    """
    eval_uuid = uuid.UUID(evaluation_id)

    with _get_sync_session() as session:
        evaluation = session.get(Evaluation, eval_uuid)
        if not evaluation:
            return {"error": "Evaluation not found"}

        evaluation.status = TaskStatus.RUNNING
        evaluation.started_at = datetime.now(timezone.utc)
        session.add(evaluation)
        session.commit()

    try:
        # TODO: integrate actual EvalScope execution here
        # For now, mark as completed with placeholder results.
        #
        # Future implementation:
        #   from app.evalscope.runner import execute_evaluation
        #   results = execute_evaluation(evaluation)

        with _get_sync_session() as session:
            evaluation = session.get(Evaluation, eval_uuid)
            if not evaluation:
                return {"error": "Evaluation not found"}

            evaluation.status = TaskStatus.COMPLETED
            evaluation.progress = 100.0
            evaluation.finished_at = datetime.now(timezone.utc)
            session.add(evaluation)
            session.commit()

        return {"status": "completed", "evaluation_id": evaluation_id}

    except Exception as exc:
        logger.exception("Evaluation %s failed", evaluation_id)
        with _get_sync_session() as session:
            evaluation = session.get(Evaluation, eval_uuid)
            if evaluation:
                evaluation.status = TaskStatus.FAILED
                evaluation.error_message = str(exc)
                evaluation.finished_at = datetime.now(timezone.utc)
                session.add(evaluation)
                session.commit()
        raise
