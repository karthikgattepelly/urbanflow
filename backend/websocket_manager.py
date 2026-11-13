"""
UrbanFlow AI - WebSocket Manager
Broadcasting real-time canonical world-state snapshots and agent events to UI clients.
"""

from typing import Set, Dict, Any
from fastapi import WebSocket
import asyncio


class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        dead = set()
        for conn in list(self.active_connections):
            try:
                await conn.send_json(message)
            except Exception:
                dead.add(conn)
        for d in dead:
            self.active_connections.discard(d)

    def broadcast_sync(self, message: Dict[str, Any]):
        """
        Synchronously dispatches broadcast if an active event loop is running.
        """
        if not self.active_connections:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))
        except RuntimeError:
            pass


ws_manager = WebSocketManager()
