import json
from typing import Any

import redis

from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_json(key: str, default: Any = None) -> Any:
    raw = redis_client.get(key)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def set_json(key: str, value: Any, ex: int | None = None) -> None:
    redis_client.set(key, json.dumps(value), ex=ex)