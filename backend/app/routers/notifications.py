from fastapi import APIRouter, Depends
from app.utils.dependencies import get_current_user
from app.services.background import notification_service, task_manager, cleanup_service
from pydantic import BaseModel
from typing import Optional


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    is_read: bool
    metadata: Optional[dict] = None
    created_at: str


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = False,
    current_user=Depends(get_current_user),
):
    notifs = notification_service.get_by_user(current_user.id, unread_only)
    unread = notification_service.get_unread_count(current_user.id)
    return NotificationListResponse(
        notifications=[NotificationResponse(**n) for n in notifs],
        total=len(notifs),
        unread_count=unread,
    )


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user=Depends(get_current_user),
):
    found = notification_service.mark_read(current_user.id, notification_id)
    if not found:
        return {"error": "Notification not found"}
    return {"status": "ok"}


@router.post("/read-all")
async def mark_all_read(
    current_user=Depends(get_current_user),
):
    count = notification_service.mark_all_read(current_user.id)
    return {"marked_read": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user=Depends(get_current_user),
):
    found = notification_service.delete(current_user.id, notification_id)
    if not found:
        return {"error": "Notification not found"}
    return {"status": "ok"}


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user=Depends(get_current_user),
):
    result = task_manager.get_result(task_id)
    if not result:
        return {"error": "Task not found"}
    return {
        "task_id": result.task_id,
        "status": result.status,
        "error": result.error,
        "created_at": result.created_at.isoformat(),
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
    }


@router.get("/tasks")
async def get_task_stats(
    current_user=Depends(get_current_user),
):
    return task_manager.get_stats()


@router.get("/cleanup")
async def get_cleanup_log(
    current_user=Depends(get_current_user),
):
    return cleanup_service.get_log()
