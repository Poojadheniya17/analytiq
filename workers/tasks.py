# workers/tasks.py
# Analytiq — Background tasks for ML pipeline

import os
import sys
import json
import logging
from datetime import datetime
from celery import Task

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

BASE_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "users")
)


def get_client_path(user_id: int, client_name: str) -> str:
    return os.path.join(BASE_DATA, str(user_id), client_name.lower().replace(" ", "_"))


def update_job_status(user_id: int, client_name: str, job_type: str, status: str, error: str = None):
    """Write job status to a JSON file so frontend can poll it."""
    client_path = get_client_path(user_id, client_name)
    os.makedirs(client_path, exist_ok=True)
    status_file = os.path.join(client_path, f"job_{job_type}.json")
    with open(status_file, "w") as f:
        json.dump({
            "status":    status,
            "job_type":  job_type,
            "error":     error,
            "updated":   datetime.utcnow().isoformat()
        }, f)


@celery_app.task(bind=True, name="workers.tasks.run_clean", max_retries=2)
def run_clean(self, user_id: int, client_name: str):
    """Background task: clean and validate uploaded CSV."""
    update_job_status(user_id, client_name, "clean", "running")
    try:
        from core.pipeline import clean_data
        result = clean_data(user_id, client_name)
        update_job_status(user_id, client_name, "clean", "done")
        return {"status": "done", "result": result}
    except Exception as e:
        logger.error(f"Clean task failed: {e}")
        update_job_status(user_id, client_name, "clean", "failed", str(e))
        raise self.retry(exc=e, countdown=5)


@celery_app.task(bind=True, name="workers.tasks.run_insights", max_retries=2)
def run_insights(self, user_id: int, client_name: str):
    """Background task: generate insights and KPIs."""
    update_job_status(user_id, client_name, "insights", "running")
    try:
        from core.insights import generate_insights
        result = generate_insights(user_id, client_name)
        update_job_status(user_id, client_name, "insights", "done")
        return {"status": "done", "result": result}
    except Exception as e:
        logger.error(f"Insights task failed: {e}")
        update_job_status(user_id, client_name, "insights", "failed", str(e))
        raise self.retry(exc=e, countdown=5)


@celery_app.task(bind=True, name="workers.tasks.run_train", max_retries=1,
                 soft_time_limit=300, time_limit=360)
def run_train(self, user_id: int, client_name: str):
    """Background task: AutoML training — runs on ML queue, 5min timeout."""
    update_job_status(user_id, client_name, "train", "running")
    try:
        from core.ml_model import train_model
        result = train_model(user_id, client_name)
        update_job_status(user_id, client_name, "train", "done")
        return {"status": "done", "result": result}
    except Exception as e:
        logger.error(f"Train task failed: {e}")
        update_job_status(user_id, client_name, "train", "failed", str(e))
        raise self.retry(exc=e, countdown=10)


@celery_app.task(bind=True, name="workers.tasks.run_narrative", max_retries=2)
def run_narrative(self, user_id: int, client_name: str, domain: str):
    """Background task: generate AI narrative."""
    update_job_status(user_id, client_name, "narrative", "running")
    try:
        from core.narrative import generate_narrative
        result = generate_narrative(user_id, client_name, domain)
        update_job_status(user_id, client_name, "narrative", "done")
        return {"status": "done"}
    except Exception as e:
        logger.error(f"Narrative task failed: {e}")
        update_job_status(user_id, client_name, "narrative", "failed", str(e))
        raise self.retry(exc=e, countdown=5)
