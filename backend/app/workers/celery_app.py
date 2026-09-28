from celery import Celery

from app.core.config import settings

celery_app = Celery("lexora", broker=settings.redis_url, include=["app.workers.tasks"])
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="lexora",
    broker_connection_retry_on_startup=True,
)
