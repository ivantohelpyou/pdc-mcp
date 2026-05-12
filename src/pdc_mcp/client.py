"""
PDC Socrata API client.

Wraps the data.wa.gov SODA API with:
- Auth via env vars (PDC_APP_TOKEN or PDC_KEY_ID + PDC_KEY_SECRET)
- 1-hour TTL cache (PDC data updates daily at most)
- SoQL injection sanitizer

Auth env vars (set in .env):
  PDC_KEY_ID      — Socrata API Key ID (HTTP Basic Auth username)
  PDC_KEY_SECRET  — Socrata API Key Secret (HTTP Basic Auth password)
  PDC_APP_TOKEN   — Simple app token (X-App-Token header)

Socrata supports two auth systems:
  API Keys (ID + Secret) → HTTP Basic Auth. Dedicated rate limit pool.
  App Tokens → X-App-Token header. Simpler to set up.
  Public data → works without auth, throttled at the shared pool.
"""

import os
import re
import time
import logging
from typing import Any

logger = logging.getLogger(__name__)

DOMAIN = "data.wa.gov"
CACHE_TTL = 3600

_cache: dict[str, tuple[float, list[dict]]] = {}


def _sanitize(value: str) -> str:
    """Strip characters that could escape a SoQL string literal."""
    return re.sub(r"['\";\\]", "", str(value))


def _cache_key(dataset_id: str, kwargs: dict) -> str:
    return f"{dataset_id}:{sorted(kwargs.items())}"


def _get_auth() -> tuple[str | None, tuple[str, str] | None]:
    key_id = os.environ.get("PDC_KEY_ID")
    key_secret = os.environ.get("PDC_KEY_SECRET")
    app_token = os.environ.get("PDC_APP_TOKEN")

    if key_id and key_secret:
        return app_token, (key_id, key_secret)
    if app_token:
        return app_token, None
    logger.warning("No PDC auth env vars set — using shared rate limit pool")
    return None, None


def query(dataset_id: str, **kwargs) -> list[dict]:
    """
    Execute a SODA query against data.wa.gov with TTL caching.

    Args:
        dataset_id: Socrata resource ID (e.g. 'kv7h-kjye')
        **kwargs:   Passed as SODA parameters (where=, limit=, offset=, order=, select=)

    Returns:
        List of result dicts.
    """
    key = _cache_key(dataset_id, kwargs)
    now = time.time()

    if key in _cache:
        ts, result = _cache[key]
        if now - ts < CACHE_TTL:
            logger.debug("Cache hit: %s", dataset_id)
            return result

    app_token, basic_auth = _get_auth()

    import requests
    headers = {"X-App-Token": app_token} if app_token else {}
    params: dict[str, Any] = {f"${k}": v for k, v in kwargs.items()}
    url = f"https://{DOMAIN}/resource/{dataset_id}.json"
    resp = requests.get(url, params=params, headers=headers,
                        auth=basic_auth, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    _cache[key] = (now, result)
    logger.info("PDC query %s → %d rows", dataset_id, len(result))
    return result


def like(field: str, value: str) -> str:
    """Case-insensitive SoQL LIKE clause."""
    return f"upper({field}) LIKE '%{_sanitize(value).upper()}%'"


def eq(field: str, value: str) -> str:
    """Exact-match SoQL equality clause."""
    return f"{field}='{_sanitize(value)}'"


def and_clauses(*clauses: str | None) -> str:
    """Join non-empty clauses with AND."""
    active = [c for c in clauses if c]
    return " AND ".join(active) if active else ""


def wrap(dataset_id: str, results: list[dict], where: str, limit: int) -> dict:
    """Standard return envelope for all PDC tools."""
    return {
        "dataset": dataset_id,
        "count": len(results),
        "limit": limit,
        "where": where,
        "results": results,
    }
