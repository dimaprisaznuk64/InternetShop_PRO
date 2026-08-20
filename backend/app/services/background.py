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
    """In-memory notification store (replaced by DB in production)."""

    def __init__(self):
        self._notifications: dict[str, list[dict]] = {}

    def create(
        self,
        user_id: str,
        ntype: str,
        title: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        import uuid

        notif = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": ntype,
            "title": title,
            "message": message,
            "is_read": False,
            "metadata": metadata,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._notifications.setdefault(user_id, []).append(notif)
        logger.info("NOTIFICATION → %s | %s: %s", user_id, ntype, title)
        return notif

    def get_by_user(
        self, user_id: str, unread_only: bool = False
    ) -> list[dict]:
        notifs = self._notifications.get(user_id, [])
        if unread_only:
            return [n for n in notifs if not n["is_read"]]
        return notifs

    def mark_read(self, user_id: str, notification_id: str) -> bool:
        for n in self._notifications.get(user_id, []):
            if n["id"] == notification_id:
                n["is_read"] = True
                return True
        return False

    def mark_all_read(self, user_id: str) -> int:
        count = 0
        for n in self._notifications.get(user_id, []):
            if not n["is_read"]:
                n["is_read"] = True
                count += 1
        return count

    def delete(self, user_id: str, notification_id: str) -> bool:
        notifs = self._notifications.get(user_id, [])
        for i, n in enumerate(notifs):
            if n["id"] == notification_id:
                notifs.pop(i)
                return True
        return False

    def get_unread_count(self, user_id: str) -> int:
        return len([n for n in self._notifications.get(user_id, []) if not n["is_read"]])


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
        # This is a placeholder — in production, use DB queries
        result["notifications_cleaned"] = 0

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
