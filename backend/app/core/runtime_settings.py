"""
Runtime-editable settings.

Reads from DB table `sitesetting` first; falls back to env/config.
Provides a thin cache so we don't hit DB on every request.
"""
import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_setting import SiteSetting
from app.core.config import settings as env_settings

# Simple in-memory cache: key -> (value, timestamp)
_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 30  # seconds

# Keys that are editable via admin UI and their env-fallback attribute names
EDITABLE_KEYS: dict[str, str] = {
    "TELEGRAM_BOT_TOKEN": "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_BOT_USERNAME": "TELEGRAM_BOT_USERNAME",
    "GEMINIGEN_API_KEY": "GEMINIGEN_API_KEY",
    "KIE_API_KEY": "KIE_API_KEY",
    "KIE_WEBHOOK_HMAC_KEY": "KIE_WEBHOOK_HMAC_KEY",
    "TIME_MACHINE_PROVIDER": "TIME_MACHINE_PROVIDER",  # "geminigen" or "kie"
    "TIME_MACHINE_MODE": "TIME_MACHINE_MODE",  # "clothing_only", "full", "full_vintage"
    "AI_API_KEY": "AI_API_KEY",
    "AI_API_BASE_URL": "AI_API_BASE_URL",
    "AI_MODEL": "AI_MODEL",
}


def _env_fallback(key: str) -> str:
    attr = EDITABLE_KEYS.get(key, key)
    return str(getattr(env_settings, attr, "") or "")


async def get_setting(db: AsyncSession, key: str) -> str:
    """Return setting value: DB override → env fallback."""
    now = time.time()
    cached = _cache.get(key)
    if cached and (now - cached[1]) < _CACHE_TTL:
        return cached[0] if cached[0] != "" else _env_fallback(key)

    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    row = result.scalars().first()
    if row and row.value:
        _cache[key] = (row.value, now)
        return row.value

    _cache[key] = ("", now)
    return _env_fallback(key)


async def set_setting(db: AsyncSession, key: str, value: str) -> None:
    """Upsert a setting in DB."""
    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    row = result.scalars().first()
    if row:
        row.value = value
    else:
        db.add(SiteSetting(key=key, value=value))
    await db.commit()
    _cache[key] = (value, time.time())


async def get_all_settings(db: AsyncSession) -> dict[str, str]:
    """Return dict of all editable settings with current effective values."""
    result = await db.execute(select(SiteSetting))
    db_rows = {r.key: r.value for r in result.scalars().all() if r.value}

    out: dict[str, str] = {}
    for key in EDITABLE_KEYS:
        out[key] = db_rows.get(key) or _env_fallback(key)
    return out


def mask_token(val: str) -> str:
    """Show only first 4 and last 4 chars of a secret."""
    if len(val) <= 10:
        return "*" * len(val)
    return val[:4] + "*" * (len(val) - 8) + val[-4:]
