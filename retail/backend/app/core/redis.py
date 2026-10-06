import json
from typing import Any

import redis

from app.core.config import settings

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None


def get_json(key: str, default: Any = None) -> Any:
    if redis_client is None:
        return default
    try:
        raw = redis_client.get(key)
        if raw is None:
            return default
        return json.loads(raw)
    except Exception:
        return default


def set_json(key: str, value: Any, ex: int | None = None) -> None:
    if redis_client is None:
        return
    try:
        redis_client.set(key, json.dumps(value), ex=ex)
    except Exception:
        pass
