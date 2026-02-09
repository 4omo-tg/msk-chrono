"""Time Machine — transform photos to look like they're from a historical year."""

import os
import uuid
from datetime import datetime
from math import ceil
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.config import settings
from app.core.runtime_settings import get_setting
from app.models.time_photo import TimePhoto
from app.schemas.time_photo import (
    CrystalBalance,
    TimePhotoCreate,
    TimePhotoHistory,
    TimePhotoOut,
)

router = APIRouter()

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

GEMINIGEN_URL = "https://api.geminigen.ai/uapi/v1/generate_image"


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _build_prompt(year: int, apply_era_style: bool) -> tuple[str, str]:
    """Return (prompt, style_description) based on the target year."""
    if not apply_era_style:
        return (
            f"Reimagine this scene as if it was from the year {year}, keeping the "
            f"modern photo quality and colors intact. Change surroundings, architecture, "
            f"fashion to match {year} but keep image quality modern.",
            "Modern quality, era-accurate surroundings",
        )
    if year < 1900:
        return (
            f"Transform this photo to look like it was taken in {year}. Apply authentic "
            f"black and white daguerreotype/vintage photography style with period-appropriate "
            f"lighting, grain, and tones. Make it look like a genuine historical photograph "
            f"from that era.",
            "Daguerreotype / vintage B&W",
        )
    if year < 1950:
        return (
            f"Transform this photo to look like it was taken in {year}. Apply authentic "
            f"sepia-toned/early 20th century photography style with appropriate grain, "
            f"contrast, and vintage tones.",
            "Sepia / early 20th-century",
        )
    if year < 1970:
        return (
            f"Transform this photo to look like it was taken in {year}. Apply mid-century "
            f"photography style with muted colors, slight film grain, and characteristic "
            f"tones of {year}s era.",
            "Mid-century muted film",
        )
    # 1970–2030
    return (
        f"Transform this photo to look like it was taken in {year}. Apply retro film "
        f"photography style with warm tones, film grain, and color palette typical of "
        f"{year}s.",
        "Retro warm film",
    )


async def _save_upload(file: UploadFile) -> str:
    """Persist the uploaded file and return a relative URL path."""
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    content = await file.read()
    filepath.write_bytes(content)
    return f"/uploads/{filename}"


async def _call_geminigen(
    prompt: str, file_path: str, db: AsyncSession = None,
) -> dict:
    """Send an image-to-image generation request to GeminiGen.AI."""
    # file_path is like "/uploads/abc.jpg" → disk path is "app/uploads/abc.jpg"
    disk_path = UPLOAD_DIR / Path(file_path).name

    api_key = await get_setting(db, "GEMINIGEN_API_KEY") if db else settings.GEMINIGEN_API_KEY
    headers = {"x-api-key": api_key}

    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(disk_path, "rb") as f:
            resp = await client.post(
                GEMINIGEN_URL,
                headers=headers,
                data={
                    "prompt": prompt,
                    "model": "nano-banana-pro",
                    "style": "Photorealistic",
                },
                files={"files": (disk_path.name, f, "image/jpeg")},
            )
    resp.raise_for_status()
    return resp.json()


async def _poll_geminigen(geminigen_uuid: str, db: AsyncSession = None) -> dict:
    """Check the status of a pending generation via histories API."""
    api_key = await get_setting(db, "GEMINIGEN_API_KEY") if db else settings.GEMINIGEN_API_KEY
    headers = {"x-api-key": api_key}
    url = "https://api.geminigen.ai/uapi/v1/histories"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # Find our generation in the list by uuid
    for item in data.get("result", []):
        if str(item.get("uuid")) == str(geminigen_uuid):
            return item

    # Fallback: return first result or empty
    return data.get("result", [{}])[0] if data.get("result") else {}


# ──────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────


@router.get("/balance", response_model=CrystalBalance)
async def get_balance(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get current Chrono-Crystal balance."""
    return CrystalBalance(chrono_crystals=current_user.chrono_crystals)


@router.post("/generate", response_model=TimePhotoOut, status_code=status.HTTP_201_CREATED)
async def generate_time_photo(
    target_year: int = Form(..., ge=1800, le=2030),
    apply_era_style: bool = Form(True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Upload a photo and start a Time-Machine transformation.

    Costs 1 Chrono-Crystal. The generation runs asynchronously on the
    GeminiGen.AI side — poll ``/check/{photo_id}`` to track progress.
    """
    # 1. Check balance
    if current_user.chrono_crystals < 1:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Недостаточно Хроно-кристаллов. Нужен минимум 1 кристалл.",
        )

    # 2. Deduct crystal
    current_user.chrono_crystals -= 1

    # 3. Save upload
    original_url = await _save_upload(file)

    # 4. Build prompt
    prompt, style_desc = _build_prompt(target_year, apply_era_style)

    # 5. Call GeminiGen.AI
    geminigen_uuid = None
    result_url = None
    photo_status = "processing"
    error_message = None

    try:
        api_resp = await _call_geminigen(prompt, original_url, db=db)
        # The API typically returns {"status": 1, "uuid": "...", ...} when queued
        geminigen_uuid = str(api_resp.get("uuid") or api_resp.get("id") or "")
        # GeminiGen returns status 2=completed, 1=processing
        api_status = api_resp.get("status")
        if api_status == 2:
            result_url = (
                api_resp.get("generate_result")
                or api_resp.get("thumbnail_url")
                or api_resp.get("last_frame_url")
            )
            if result_url:
                result_url = result_url.replace("_600px", "")
            photo_status = "completed"
        else:
            photo_status = "processing"
    except httpx.HTTPStatusError as exc:
        photo_status = "failed"
        error_message = f"GeminiGen API error: {exc.response.status_code} — {exc.response.text[:300]}"
        current_user.chrono_crystals += 1  # Refund on API error
    except Exception as exc:  # noqa: BLE001
        photo_status = "failed"
        error_message = f"GeminiGen API request failed: {exc}"
        current_user.chrono_crystals += 1  # Refund on error

    # 6. Save TimePhoto record
    time_photo = TimePhoto(
        user_id=current_user.id,
        original_image_url=original_url,
        result_image_url=result_url,
        target_year=target_year,
        apply_era_style=apply_era_style,
        style_applied=style_desc,
        prompt_used=prompt,
        geminigen_uuid=geminigen_uuid,
        status=photo_status,
        error_message=error_message,
        cost=1,
        completed_at=datetime.utcnow() if photo_status == "completed" else None,
    )
    db.add(time_photo)
    await db.commit()
    await db.refresh(time_photo)

    return time_photo


@router.get("/history", response_model=TimePhotoHistory)
async def get_history(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Paginated list of the user's Time-Machine generations."""
    # Total count
    total_q = await db.execute(
        select(sa_func.count()).select_from(TimePhoto).where(TimePhoto.user_id == current_user.id)
    )
    total = total_q.scalar() or 0
    pages = ceil(total / per_page) if per_page else 1

    # Fetch page
    offset = (page - 1) * per_page
    rows_q = await db.execute(
        select(TimePhoto)
        .where(TimePhoto.user_id == current_user.id)
        .order_by(TimePhoto.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    items = rows_q.scalars().all()

    return TimePhotoHistory(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{photo_id}", response_model=TimePhotoOut)
async def get_time_photo(
    photo_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get details of a specific Time-Machine photo."""
    result = await db.execute(
        select(TimePhoto).where(
            TimePhoto.id == photo_id,
            TimePhoto.user_id == current_user.id,
        )
    )
    photo = result.scalars().first()
    if not photo:
        raise HTTPException(status_code=404, detail="Фото не найдено")
    return photo


@router.post("/check/{photo_id}", response_model=TimePhotoOut)
async def check_generation(
    photo_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Poll GeminiGen.AI for the status of a pending generation."""
    result = await db.execute(
        select(TimePhoto).where(
            TimePhoto.id == photo_id,
            TimePhoto.user_id == current_user.id,
        )
    )
    photo = result.scalars().first()
    if not photo:
        raise HTTPException(status_code=404, detail="Фото не найдено")

    # Already terminal — nothing to poll
    if photo.status in ("completed", "failed"):
        return photo

    if not photo.geminigen_uuid:
        raise HTTPException(
            status_code=400,
            detail="Нет UUID для проверки статуса генерации",
        )

    try:
        poll_resp = await _poll_geminigen(photo.geminigen_uuid, db=db)
    except httpx.HTTPStatusError as exc:
        photo.status = "failed"
        photo.error_message = f"Poll error: {exc.response.status_code}"
        await db.commit()
        await db.refresh(photo)
        return photo
    except Exception as exc:  # noqa: BLE001
        photo.status = "failed"
        photo.error_message = f"Poll request failed: {exc}"
        await db.commit()
        await db.refresh(photo)
        return photo

    api_status = poll_resp.get("status")

    # GeminiGen: status 2 = completed, 3 = failed, 1 = processing
    if api_status == 2:
        # Try generate_result first, then thumbnail_url as fallback
        result_url = (
            poll_resp.get("generate_result")
            or poll_resp.get("thumbnail_url")
            or poll_resp.get("last_frame_url")
        )
        if result_url:
            # Replace _600px thumbnail with full size if possible
            full_url = result_url.replace("_600px", "")
            photo.result_image_url = full_url
            photo.status = "completed"
            photo.completed_at = datetime.utcnow()
        else:
            photo.status = "completed"
            photo.completed_at = datetime.utcnow()
            photo.error_message = "Generation completed but no image URL returned"
    elif api_status == 3 or poll_resp.get("error_message"):
        photo.status = "failed"
        photo.error_message = poll_resp.get("error_message", "Generation failed on provider side")
    # else still processing (status=1) — keep status as-is

    await db.commit()
    await db.refresh(photo)
    return photo
