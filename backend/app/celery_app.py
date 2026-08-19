from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "internetshop",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

celery_app.conf.beat_schedule = {
    "cleanup-notifications-hourly": {
        "task": "app.services.celery_tasks.cleanup_old_notifications",
        "schedule": crontab(minute=0, hour="*/1"),
    },
    "cleanup-expired-promos-daily": {
        "task": "app.services.celery_tasks.cleanup_expired_promos",
        "schedule": crontab(minute=0, hour=2),
    },
    "send-daily-stats": {
        "task": "app.services.celery_tasks.generate_daily_stats",
        "schedule": crontab(minute=30, hour=8),
    },
}

celery_app.autodiscover_tasks(["app.services"])
