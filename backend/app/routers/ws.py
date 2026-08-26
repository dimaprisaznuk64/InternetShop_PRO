from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import async_session
from app.models.order import Order
from app.services.websocket import ws_manager
from app.utils.security import decode_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def _get_order_owner(order_id: str) -> str | None:
    async with async_session() as db:
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        return order.user_id if order else None


@router.websocket("/ws/orders/{order_id}")
async def order_tracking_ws(ws: WebSocket, order_id: str, token: str = ""):
    """WebSocket endpoint for real-time order status tracking.

    Connect: ws://host/ws/orders/{order_id}?token={jwt}
    """
    if not token:
        await ws.close(code=4001, reason="Missing token")
        return

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return

    owner_id = await _get_order_owner(order_id)
    if not owner_id:
        await ws.close(code=4004, reason="Order not found")
        return

    if owner_id != user_id:
        await ws.close(code=4003, reason="Access denied")
        return

    await ws_manager.connect(ws, order_id, user_id)

    # Send current status immediately
    async with async_session() as db:
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order:
            status_val = order.status.value if hasattr(order.status, "value") else order.status
            await ws.send_json({
                "type": "status_update",
                "status": status_val,
                "order_id": order_id,
            })

    try:
        while True:
            data = await ws.receive_text()
            # Client can send ping
            if data == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws, order_id, user_id)
