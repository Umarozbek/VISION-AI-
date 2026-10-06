import json
from datetime import datetime, timezone

import httpx
import redis

from config import AI_API_KEY, BACKEND_URL, REDIS_URL


class EventPublisher:
    def __init__(self):
        # decode_responses=True — faqat JSON string uchun (broadcast)
        self._redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.headers = {"X-API-Key": AI_API_KEY}

    def broadcast(self, payload: dict) -> None:
        """Faqat Redis pubsub ga yuboradi (WebSocket real-time uchun)."""
        message = {
            "type": "detection",
            "data": {**payload, "timestamp": datetime.now(timezone.utc).isoformat()},
        }
        try:
            self._redis.publish("analytics:live", json.dumps(message))
        except Exception as exc:
            print(f"Redis broadcast xato: {exc}")

    def publish(self, client: httpx.Client, payload: dict) -> None:
        """Redis broadcast + HTTP post (bitta event uchun)."""
        self.broadcast(payload)
        try:
            client.post(
                f"{BACKEND_URL}/analytics/events",
                json=payload,
                headers=self.headers,
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            print(f"Event publish failed: {exc}")

    def update_status(self, client: httpx.Client, camera_id: int, status: str) -> None:
        try:
            client.patch(
                f"{BACKEND_URL}/cameras/{camera_id}/status",
                json={
                    "processing_status": status,
                    "last_frame_at": datetime.now(timezone.utc).isoformat(),
                },
                headers=self.headers,
                timeout=5.0,
            )
        except httpx.HTTPError:
            pass