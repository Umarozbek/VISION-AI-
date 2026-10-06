import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.redis import redis_client
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/analytics")
async def analytics_ws(websocket: WebSocket):
    await manager.connect(websocket)
    pubsub = redis_client.pubsub()
    pubsub.subscribe("analytics:live")

    async def redis_listener():
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
            if message and message.get("data"):
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast(data)
                except (json.JSONDecodeError, TypeError):
                    pass
            await asyncio.sleep(0.1)

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        listener_task.cancel()
        manager.disconnect(websocket)
