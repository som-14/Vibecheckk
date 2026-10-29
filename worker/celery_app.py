# Plain-English description: Configures the Celery application with Redis broker for asynchronous video processing.
# Note: Azure Service Bus is the production equivalent for message queuing.

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "vibecheck_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_timeout=1.0,
    broker_connection_retry=False,
    broker_connection_max_retries=1,
    broker_transport_options={
        "socket_timeout": 1.0,
        "socket_connect_timeout": 1.0
    },
    redis_socket_timeout=1.0,
    redis_socket_connect_timeout=1.0,
)
