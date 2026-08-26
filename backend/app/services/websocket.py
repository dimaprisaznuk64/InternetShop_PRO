import json
import logging
from fastapi import WebSocket
from app.utils.security import decode_token

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per order for real-time tracking."""

    def __init__(self):
        # order_id -> {user_id: [WebSocket, ...]}
        self._connections: dict[str, dict[str, list[WebSocket]]] = {}

    async def connect(self, ws: WebSocket, order_id: str, user_id: str):
        await ws.accept()
        if order_id not in self._connections:
            self._connections[order_id] = {}
        if user_id not in self._connections[order_id]:
            self._connections[order_id][user_id] = []
        self._connections[order_id][user_id].append(ws)
        logger.info("WS connected: order=%s user=%s", order_id, user_id)

    def disconnect(self, ws: WebSocket, order_id: str, user_id: str):
        if order_id in self._connections and user_id in self._connections[order_id]:
            self._connections[order_id][user_id] = [
                s for s in self._connections[order_id][user_id] if s != ws
            ]
            if not self._connections[order_id][user_id]:
                del self._connections[order_id][user_id]
            if not self._connections[order_id]:
                del self._connections[order_id]
        logger.info("WS disconnected: order=%s user=%s", order_id, user_id)

    async def broadcast(self, order_id: str, data: dict):
        if order_id not in self._connections:
            return
        message = json.dumps(data)
        dead: list[tuple[str, WebSocket]] = []
        for user_id, sockets in self._connections[order_id].items():
            for ws in sockets:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append((user_id, ws))
        for uid, ws in dead:
            self.disconnect(ws, order_id, uid)


ws_manager = ConnectionManager()
