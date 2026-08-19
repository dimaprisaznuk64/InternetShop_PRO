import pytest
import asyncio
from app.services.background import (
    EmailService,
    NotificationService,
    BackgroundTaskManager,
    CleanupService,
)


@pytest.fixture
def email_svc():
    return EmailService()


@pytest.fixture
def notif_svc():
    return NotificationService()


class TestEmailService:
    @pytest.mark.asyncio
    async def test_send(self, email_svc):
        result = await email_svc.send("test@example.com", "Test", "Hello")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_welcome(self, email_svc):
        result = await email_svc.send_welcome("test@example.com", "John")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_order_confirmation(self, email_svc):
        result = await email_svc.send_order_confirmation("test@example.com", "order-123", "$99.99")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_order_status_change(self, email_svc):
        result = await email_svc.send_order_status_change("test@example.com", "order-123", "shipped")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_payment_confirmation(self, email_svc):
        result = await email_svc.send_payment_confirmation("test@example.com", "order-123", "$50.00")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_payment_failed(self, email_svc):
        result = await email_svc.send_payment_failed("test@example.com", "order-123")
        assert result is True


class TestNotificationService:
    def test_create_and_get(self, notif_svc):
        notif = notif_svc.create("user-1", "welcome", "Welcome!", "Hello there!")
        assert notif["user_id"] == "user-1"
        assert notif["type"] == "welcome"
        assert notif["is_read"] is False

        notifs = notif_svc.get_by_user("user-1")
        assert len(notifs) == 1
        assert notifs[0]["id"] == notif["id"]

    def test_get_empty(self, notif_svc):
        notifs = notif_svc.get_by_user("nonexistent")
        assert notifs == []

    def test_unread_only(self, notif_svc):
        n1 = notif_svc.create("user-1", "welcome", "Welcome", "Hello")
        n2 = notif_svc.create("user-1", "system", "System", "Update")
        notif_svc.mark_read("user-1", n1["id"])

        unread = notif_svc.get_by_user("user-1", unread_only=True)
        assert len(unread) == 1
        assert unread[0]["id"] == n2["id"]

    def test_mark_read(self, notif_svc):
        n = notif_svc.create("user-1", "welcome", "Welcome", "Hello")
        result = notif_svc.mark_read("user-1", n["id"])
        assert result is True
        assert notif_svc.get_by_user("user-1")[0]["is_read"] is True

    def test_mark_read_not_found(self, notif_svc):
        result = notif_svc.mark_read("user-1", "nonexistent")
        assert result is False

    def test_mark_all_read(self, notif_svc):
        notif_svc.create("user-1", "welcome", "W1", "M1")
        notif_svc.create("user-1", "system", "W2", "M2")
        count = notif_svc.mark_all_read("user-1")
        assert count == 2
        assert notif_svc.get_unread_count("user-1") == 0

    def test_delete(self, notif_svc):
        n = notif_svc.create("user-1", "welcome", "Welcome", "Hello")
        result = notif_svc.delete("user-1", n["id"])
        assert result is True
        assert len(notif_svc.get_by_user("user-1")) == 0

    def test_delete_not_found(self, notif_svc):
        result = notif_svc.delete("user-1", "nonexistent")
        assert result is False

    def test_get_unread_count(self, notif_svc):
        notif_svc.create("user-1", "welcome", "W1", "M1")
        notif_svc.create("user-1", "system", "W2", "M2")
        assert notif_svc.get_unread_count("user-1") == 2

    def test_multiple_users(self, notif_svc):
        notif_svc.create("user-1", "welcome", "W1", "M1")
        notif_svc.create("user-2", "system", "W2", "M2")
        assert len(notif_svc.get_by_user("user-1")) == 1
        assert len(notif_svc.get_by_user("user-2")) == 1

    def test_notification_with_metadata(self, notif_svc):
        n = notif_svc.create(
            "user-1", "order_created", "Order", "Placed",
            {"order_id": "abc-123", "total": 99.99},
        )
        assert n["metadata"]["order_id"] == "abc-123"
        assert n["metadata"]["total"] == 99.99


class TestBackgroundTaskManager:
    @pytest.mark.asyncio
    async def test_submit_and_get_result(self):
        mgr = BackgroundTaskManager(max_workers=1)
        await mgr.start()

        async def dummy(x):
            return x * 2

        task_id = await mgr.submit(dummy, 5)
        await asyncio.sleep(0.5)

        result = mgr.get_result(task_id)
        assert result is not None
        assert result.status == "completed"
        assert result.result == 10

        await mgr.stop()

    @pytest.mark.asyncio
    async def test_task_failure(self):
        mgr = BackgroundTaskManager(max_workers=1)
        await mgr.start()

        async def failing():
            raise ValueError("boom")

        task_id = await mgr.submit(failing)
        await asyncio.sleep(0.5)

        result = mgr.get_result(task_id)
        assert result is not None
        assert result.status == "failed"
        assert "boom" in result.error

        await mgr.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        mgr = BackgroundTaskManager(max_workers=1)
        await mgr.start()

        async def slow():
            await asyncio.sleep(10)

        await mgr.submit(slow)
        stats = mgr.get_stats()
        assert stats["running"] is True
        assert stats["pending"] >= 0

        await mgr.stop()

    @pytest.mark.asyncio
    async def test_get_result_nonexistent(self):
        mgr = BackgroundTaskManager()
        result = mgr.get_result("nonexistent")
        assert result is None


class TestCleanupService:
    @pytest.mark.asyncio
    async def test_run_once(self):
        svc = CleanupService()
        result = await svc.run_once()
        assert "timestamp" in result
        assert "notifications_cleaned" in result

    @pytest.mark.asyncio
    async def test_get_log(self):
        svc = CleanupService()
        await svc.run_once()
        log = svc.get_log()
        assert len(log) == 1
