import logging
from datetime import datetime, timedelta
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.services.celery_tasks.send_email")
def send_email(self, to: str, subject: str, body: str):
    logger.info("CELERY EMAIL -> %s | Subject: %s", to, subject)
    return {"to": to, "subject": subject, "status": "sent", "timestamp": datetime.utcnow().isoformat()}


@celery_app.task(bind=True, name="app.services.celery_tasks.send_welcome_email")
def send_welcome_email(self, to: str, username: str):
    return send_email(to, "Welcome to Internet Shop PRO!", f"Hello {username}, welcome!")


@celery_app.task(bind=True, name="app.services.celery_tasks.send_order_confirmation")
def send_order_confirmation(self, to: str, order_id: str, total: str):
    return send_email(
        to,
        f"Order #{order_id[:8]} confirmed",
        f"Your order for {total} has been placed successfully.",
    )


@celery_app.task(bind=True, name="app.services.celery_tasks.send_order_status_change")
def send_order_status_change(self, to: str, order_id: str, status: str):
    return send_email(
        to,
        f"Order #{order_id[:8]} status update",
        f"Your order status has been changed to: {status}.",
    )


@celery_app.task(bind=True, name="app.services.celery_tasks.send_payment_confirmation")
def send_payment_confirmation(self, to: str, order_id: str, amount: str):
    return send_email(
        to,
        f"Payment received for order #{order_id[:8]}",
        f"We received your payment of {amount}. Thank you!",
    )


@celery_app.task(bind=True, name="app.services.celery_tasks.send_payment_failed")
def send_payment_failed(self, to: str, order_id: str):
    return send_email(
        to,
        f"Payment failed for order #{order_id[:8]}",
        "Your payment could not be processed. Please try again.",
    )


@celery_app.task(bind=True, name="app.services.celery_tasks.cleanup_old_notifications")
def cleanup_old_notifications(self):
    logger.info("CELERY: Running cleanup_old_notifications")
    return {
        "task": "cleanup_old_notifications",
        "cleaned": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


@celery_app.task(bind=True, name="app.services.celery_tasks.cleanup_expired_promos")
def cleanup_expired_promos(self):
    logger.info("CELERY: Running cleanup_expired_promos")
    return {
        "task": "cleanup_expired_promos",
        "cleaned": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


@celery_app.task(bind=True, name="app.services.celery_tasks.generate_daily_stats")
def generate_daily_stats(self):
    logger.info("CELERY: Running generate_daily_stats")
    return {
        "task": "generate_daily_stats",
        "generated_at": datetime.utcnow().isoformat(),
    }


@celery_app.task(bind=True, name="app.services.celery_tasks.send_bulk_email")
def send_bulk_email(self, recipients: list, subject: str, body: str):
    results = []
    for recipient in recipients:
        result = send_email(recipient, subject, body)
        results.append({"recipient": recipient, "result": result})
    return {"total_sent": len(results), "results": results}
