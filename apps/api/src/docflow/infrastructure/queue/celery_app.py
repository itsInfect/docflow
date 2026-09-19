from celery import Celery  # type: ignore[import-untyped]

from docflow.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "docflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)
