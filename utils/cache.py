import json
import os
import time
from typing import Optional, Any
from config import settings

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")


def _ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(service: str, query: str) -> str:
    safe_query = query.replace("/", "_").replace(" ", "_").replace(":", "_")
    return f"{service}_{safe_query}.json"


def get_cache(service: str, query: str) -> Optional[Any]:
    if not settings.cache_enabled:
        return None
    _ensure_cache_dir()
    key = _cache_key(service, query)
    path = os.path.join(CACHE_DIR, key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if time.time() - data.get("timestamp", 0) > settings.cache_ttl:
            os.remove(path)
            return None
        return data.get("result")
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def set_cache(service: str, query: str, result: Any):
    if not settings.cache_enabled:
        return
    _ensure_cache_dir()
    key = _cache_key(service, query)
    path = os.path.join(CACHE_DIR, key)
    try:
        with open(path, "w") as f:
            json.dump({"timestamp": time.time(), "result": result}, f)
    except OSError:
        pass


def clear_cache():
    if os.path.exists(CACHE_DIR):
        for fname in os.listdir(CACHE_DIR):
            fpath = os.path.join(CACHE_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except OSError:
                pass
