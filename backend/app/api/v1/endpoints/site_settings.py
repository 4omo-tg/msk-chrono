from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.runtime_settings import (
    EDITABLE_KEYS, get_all_settings, set_setting, mask_token,
)

router = APIRouter()


class SettingsOut(BaseModel):
    key: str
    value: str  # masked
    has_value: bool


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("/", response_model=list[SettingsOut])
async def read_settings(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get all editable settings (tokens masked)."""
    all_s = await get_all_settings(db)
    out = []
    for key in EDITABLE_KEYS:
        val = all_s.get(key, "")
        is_secret = "TOKEN" in key or "KEY" in key
        out.append(SettingsOut(
            key=key,
            value=mask_token(val) if (is_secret and val) else val,
            has_value=bool(val),
        ))
    return out


@router.put("/")
async def update_setting(
    payload: SettingUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Update a single setting."""
    if payload.key not in EDITABLE_KEYS:
        raise HTTPException(400, f"Unknown setting key: {payload.key}")
    await set_setting(db, payload.key, payload.value)
    return {"ok": True, "key": payload.key}
