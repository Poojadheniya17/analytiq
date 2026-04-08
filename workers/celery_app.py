# workers/celery_app.py
# Analytiq — Celery configuration for background ML jobs

import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "analytiq",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.tasks"]
)

celery_app.conf.update(
    task_serializer          = "json",
    result_serializer        = "json",
    accept_content           = ["json"],
    result_expires           = 3600,        # results expire after 1 hour
    task_track_started       = True,
    task_acks_late           = True,        # ack after task completes, not before
    worker_prefetch_multiplier = 1,         # one task at a time per worker
    task_routes = {
        "workers.tasks.run_clean":     {"queue": "analytics"},
        "workers.tasks.run_insights":  {"queue": "analytics"},
        "workers.tasks.run_train":     {"queue": "ml"},       # ML on separate queue
        "workers.tasks.run_narrative": {"queue": "analytics"},
        "workers.tasks.run_export":    {"queue": "analytics"},
    }
)
