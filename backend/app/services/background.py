import asyncio
import json
import logging
from datetime import datetime, timedelta, UTC
from typing import Any, Callable, Optional
from dataclasses import dataclass, field

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Try to import Celery; fall back to asyncio-based tasks
try:
    from app.services.celery_tasks import (
        send_welcome_email,
        send_order_confirmation,
        send_order_status_change,
        send_payment_confirmation,
        send_payment_failed,
    )
    USE_CELERY = True
    logger.info("Using Celery for background tasks")
except ImportError:
    USE_CELERY = False
    logger.info("Celery not available, using asyncio-based background tasks")


@dataclass
class TaskResult:
    task_id: str
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None


class EmailService:
    """Simulated email service — logs emails instead of sending."""

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
    ) -> bool:
        logger.info("EMAIL → %s | Subject: %s | Body: %s", to, subject, body[:100])
        return True

    async def send_welcome(self, to: str, username: str) -> bool:
        return await self.send(
            to=to,
            subject="Welcome to Internet Shop PRO!",
            body=f"Hello {username}, welcome to our shop!",
        )

    async def send_order_confirmation(
        self, to: str, order_id: str, total: str
    ) -> bool:
        return await self.send(
            to=to,
            subject=f"Order #{order_id[:8]} confirmed",
            body=f"Your order for {total} has been placed successfully.",
        )

    async def send_order_status_change(
        self, to: str, order_id: str, status: str
    ) -> bool:
        return await self.send(
            to=to,
            subject=f"Order #{order_id[:8]} status update",
            body=f"Your order status has been changed to: {status}.",
        )

    async def send_payment_confirmation(
        self, to: str, order_id: str, amount: str
    ) -> bool:
        return await self.send(
            to=to,
            subject=f"Payment received for order #{order_id[:8]}",
            body=f"We received your payment of {amount}. Thank you!",
        )

    async def send_payment_failed(self, to: str, order_id: str) -> bool:
        return await self.send(
            to=to,
            subject=f"Payment failed for order #{order_id[:8]}",
            body="Your payment could not be processed. Please try again.",
        )


class NotificationService:
    """DB-backed notification store (PostgreSQL via SQLAlchemy)."""

    @staticmethod
    def _serialize(notif) -> dict:
        metadata = None
        if notif.metadata_json:
            try:
                metadata = json.loads(notif.metadata_json)
            except (TypeError, ValueError):
                metadata = None
        ntype = (
            notif.type.value if hasattr(notif.type, "value") else notif.type
        )
        return {
            "id": notif.id,
            "user_id": notif.user_id,
            "type": ntype,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read,
            "metadata": metadata,
            "created_at": (
                notif.created_at.isoformat() if notif.created_at else None
            ),
        }

    async def create(
        self,
        db,
        user_id: str,
        ntype: str,
        title: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        from app.models.notification import Notification, NotificationType

        try:
            ntype_enum = NotificationType(ntype)
        except ValueError:
            ntype_enum = NotificationType.system

        notif = Notification(
            user_id=user_id,
            type=ntype_enum,
            title=title,
            message=message,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        logger.info("NOTIFICATION → %s | %s: %s", user_id, ntype, title)
        return self._serialize(notif)

    async def get_by_user(
        self, db, user_id: str, unread_only: bool = False
    ) -> list[dict]:
        from sqlalchemy import select
        from app.models.notification import Notification

        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc())
        result = await db.execute(stmt)
        return [self._serialize(n) for n in result.scalars().all()]

    async def get_unread_count(self, db, user_id: str) -> int:
        from sqlalchemy import select, func
        from app.models.notification import Notification

        result = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar_one()

    async def mark_read(self, db, user_id: str, notification_id: str) -> bool:
        from sqlalchemy import select
        from app.models.notification import Notification

        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notif = result.scalar_one_or_none()
        if not notif:
            return False
        notif.is_read = True
        await db.commit()
        return True

    async def mark_all_read(self, db, user_id: str) -> int:
        from sqlalchemy import update
        from app.models.notification import Notification

        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await db.commit()
        return result.rowcount or 0

    async def delete(self, db, user_id: str, notification_id: str) -> bool:
        from sqlalchemy import delete as sa_delete
        from app.models.notification import Notification

        result = await db.execute(
            sa_delete(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        await db.commit()
        return (result.rowcount or 0) > 0


class BackgroundTaskManager:
    """Manages background tasks with Celery (preferred) or asyncio workers."""

    def __init__(self, max_workers: int = 3):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._results: dict[str, TaskResult] = {}
        self._max_workers = max_workers
        self._running = False
        self._task_counter = 0
        self._use_celery = USE_CELERY
        self._celery_available = False

    async def start(self):
        if self._running:
            return
        self._running = True
        if self._use_celery:
            try:
                from app.celery_app import celery_app
                inspect = celery_app.control.inspect(timeout=1.0)
                result = inspect.ping()
                if result is not None:
                    self._celery_available = True
                    logger.info("Background task manager started (Celery mode)")
                else:
                    self._celery_available = False
                    logger.info("Celery workers not found, falling back to asyncio")
            except Exception:
                self._celery_available = False
                logger.info("Celery broker unavailable, falling back to asyncio")
        if not self._celery_available:
            for i in range(self._max_workers):
                worker = asyncio.create_task(self._worker(f"worker-{i}"))
                self._workers.append(worker)
            logger.info("Background task manager started with %d asyncio workers", self._max_workers)

    async def stop(self):
        self._running = False
        for w in self._workers:
            w.cancel()
        self._workers.clear()
        logger.info("Background task manager stopped")

    async def submit(
        self, func: Callable, *args, **kwargs
    ) -> str:
        self._task_counter += 1
        task_id = f"task-{self._task_counter}"
        self._results[task_id] = TaskResult(task_id=task_id)

        if self._celery_available:
            celery_task = self._map_to_celery_task(func)
            if celery_task:
                try:
                    result = celery_task.apply_async(
                        args=args, kwargs=kwargs, timeout=5
                    )
                    self._results[task_id].status = "submitted"
                    self._results[task_id].result = {"celery_task_id": result.id}
                    return task_id
                except Exception as e:
                    logger.warning("Celery submit failed, falling back to asyncio: %s", e)

        # Fallback to asyncio queue
        await self._queue.put((task_id, func, args, kwargs))
        return task_id

    def _map_to_celery_task(self, func: Callable):
        """Map email_service methods to Celery tasks."""
        from app.services.background import email_service
        mapping = {
            email_service.send_welcome: send_welcome_email,
            email_service.send_order_confirmation: send_order_confirmation,
            email_service.send_order_status_change: send_order_status_change,
            email_service.send_payment_confirmation: send_payment_confirmation,
            email_service.send_payment_failed: send_payment_failed,
        }
        return mapping.get(func)

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        return self._results.get(task_id)

    def get_stats(self) -> dict:
        pending = self._queue.qsize()
        completed = sum(1 for r in self._results.values() if r.status == "completed")
        failed = sum(1 for r in self._results.values() if r.status == "failed")
        return {
            "pending": pending,
            "completed": completed,
            "failed": failed,
            "total": len(self._results),
            "running": self._running,
        }

    async def _worker(self, name: str):
        while self._running:
            try:
                task_id, func, args, kwargs = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            result = self._results.get(task_id)
            if result:
                result.status = "running"
                try:
                    output = await func(*args, **kwargs)
                    result.status = "completed"
                    result.result = output
                except Exception as e:
                    result.status = "failed"
                    result.error = str(e)
                    logger.error("Task %s failed: %s", task_id, e)
                finally:
                    result.completed_at = datetime.now(UTC)


class CleanupService:
    """Scheduled cleanup tasks."""

    def __init__(self, interval_seconds: int = 3600):
        self._interval = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._cleanup_log: list[dict] = []

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Cleanup service started (interval: %ds)", self._interval)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Cleanup service stopped")

    async def run_once(self) -> dict:
        return await self._cleanup()

    async def _run_loop(self):
        while self._running:
            await asyncio.sleep(self._interval)
            if self._running:
                await self._cleanup()

    async def _cleanup(self) -> dict:
        result = {
            "notifications_cleaned": 0,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Cleanup old read notifications (> 30 days)
        try:
            from sqlalchemy import delete
            from app.database import async_session
            from app.models.notification import Notification

            cutoff = datetime.now(UTC) - timedelta(days=30)
            async with async_session() as session:
                db_result = await session.execute(
                    delete(Notification).where(
                        Notification.is_read.is_(True),
                        Notification.created_at < cutoff,
                    )
                )
                await session.commit()
                result["notifications_cleaned"] = db_result.rowcount or 0
        except Exception as e:
            logger.warning("Notification cleanup failed: %s", e)

        self._cleanup_log.append(result)
        if len(self._cleanup_log) > 100:
            self._cleanup_log = self._cleanup_log[-50:]

        logger.info("Cleanup completed: %s", result)
        return result

    def get_log(self) -> list[dict]:
        return list(self._cleanup_log)


email_service = EmailService()
notification_service = NotificationService()
task_manager = BackgroundTaskManager()
cleanup_service = CleanupService()
