# Plain-English description: Initializes the Celery client instance for enqueuing video processing tasks.

from celery import Celery
from backend.config import REDIS_URL

celery_app = Celery(
    "vibecheck_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
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
