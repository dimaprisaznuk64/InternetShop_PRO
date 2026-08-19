import pytest
from unittest.mock import patch, MagicMock
from app.celery_app import celery_app
from app.services.celery_tasks import (
    send_email,
    send_welcome_email,
    send_order_confirmation,
    send_order_status_change,
    send_payment_confirmation,
    send_payment_failed,
    cleanup_old_notifications,
    cleanup_expired_promos,
    generate_daily_stats,
    send_bulk_email,
)


class TestCeleryApp:
    def test_celery_app_exists(self):
        assert celery_app is not None

    def test_celery_app_name(self):
        assert celery_app.main == "internetshop"

    def test_celery_conf(self):
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.result_expires == 3600

    def test_beat_schedule_exists(self):
        assert "cleanup-notifications-hourly" in celery_app.conf.beat_schedule
        assert "cleanup-expired-promos-daily" in celery_app.conf.beat_schedule
        assert "send-daily-stats" in celery_app.conf.beat_schedule


class TestCeleryTasks:
    def test_send_email(self):
        result = send_email.run("test@example.com", "Test Subject", "Test body")
        assert result["to"] == "test@example.com"
        assert result["subject"] == "Test Subject"
        assert result["status"] == "sent"
        assert "timestamp" in result

    def test_send_welcome_email(self):
        result = send_welcome_email.run("test@example.com", "John")
        assert result["to"] == "test@example.com"
        assert result["status"] == "sent"

    def test_send_order_confirmation(self):
        result = send_order_confirmation.run("test@example.com", "order-123-456", "$99.99")
        assert result["to"] == "test@example.com"
        assert result["status"] == "sent"

    def test_send_order_status_change(self):
        result = send_order_status_change.run("test@example.com", "order-123-456", "shipped")
        assert result["to"] == "test@example.com"
        assert result["status"] == "sent"

    def test_send_payment_confirmation(self):
        result = send_payment_confirmation.run("test@example.com", "order-123-456", "$50.00")
        assert result["to"] == "test@example.com"
        assert result["status"] == "sent"

    def test_send_payment_failed(self):
        result = send_payment_failed.run("test@example.com", "order-123-456")
        assert result["to"] == "test@example.com"
        assert result["status"] == "sent"

    def test_cleanup_old_notifications(self):
        result = cleanup_old_notifications.run()
        assert result["task"] == "cleanup_old_notifications"
        assert "timestamp" in result

    def test_cleanup_expired_promos(self):
        result = cleanup_expired_promos.run()
        assert result["task"] == "cleanup_expired_promos"
        assert "timestamp" in result

    def test_generate_daily_stats(self):
        result = generate_daily_stats.run()
        assert result["task"] == "generate_daily_stats"
        assert "generated_at" in result

    def test_send_bulk_email(self):
        result = send_bulk_email.run(
            ["a@test.com", "b@test.com"], "Bulk", "Hello everyone"
        )
        assert result["total_sent"] == 2
        assert len(result["results"]) == 2
