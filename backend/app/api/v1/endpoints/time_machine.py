"""Time Machine — transform photos to look like they're from a historical year.

Supports two providers:
- GeminiGen.AI (default)
- KIE AI (nano-banana-pro model)

Modes:
- clothing_only: Only update clothing to period-appropriate fashion
- full: Update clothing + architecture/environment  
- full_vintage: Full update + vintage photo style (B&W, sepia, grain, vignette)
"""

import os
import uuid
import base64
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Optional

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
    TimeMachineConfig,
)

router = APIRouter()

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# API URLs
GEMINIGEN_URL = "https://api.geminigen.ai/uapi/v1/generate_image"
KIE_API_BASE = "https://api.kie.ai"
KIE_FILE_UPLOAD_URL = "https://kieai.redpandaai.co/api/file-base64-upload"


# ──────────────────────────────────────────────────────────────────────
# Prompt Templates
# ──────────────────────────────────────────────────────────────────────

def _get_era_style_description(year: int) -> tuple[str, str]:
    """Return (vintage_style_prompt, style_label) for the target year."""
    if year < 1900:
        return (
            "Apply authentic 19th century daguerreotype photography style: "
            "true black and white with high contrast, visible grain and texture, "
            "soft vignette around edges, slightly faded corners, period-appropriate "
            "lighting with dramatic shadows.",
            "Daguerreotype / vintage B&W"
        )
    if year < 1940:
        return (
            "Apply early 20th century photography style: sepia-toned or slightly "
            "desaturated colors, visible film grain, soft focus edges, warm brownish "
            "tones characteristic of early color or hand-tinted photographs.",
            "Sepia / early 20th-century"
        )
    if year < 1970:
        return (
            "Apply 1950s photography style: muted desaturated colors, subtle film grain, "
            "soft contrast, slight vignette, and warm tonal range characteristic of "
            "mid-century Kodachrome or Ektachrome film stock.",
            "Mid-century muted film"
        )
    if year < 2000:
        return (
            "Apply retro film photography style with warm tones, visible film grain, "
            "slightly faded colors, light leaks, and color palette typical of "
            "1970s-1990s consumer film photography.",
            "Retro warm film"
        )
    return (
        "Modern digital photography style with natural colors.",
        "Modern digital"
    )


def _get_clothing_prompt(year: int) -> str:
    """Return clothing/fashion description for the target year."""
    if year < 1850:
        return (
            "Update clothing to early 19th century fashion: men in tailcoats, waistcoats, "
            "cravats, and top hats; women in empire-waist dresses with high necklines, "
            "bonnets, and shawls."
        )
    if year < 1900:
        return (
            "Update clothing to Victorian era fashion: men in frock coats, bowler hats, "
            "and pocket watches; women in bustle dresses, corsets, high collars, "
            "and elaborate hats."
        )
    if year < 1930:
        return (
            "Update clothing to early 20th century fashion: men in three-piece suits "
            "with wide lapels, bowler or fedora hats, pocket watches; women in "
            "long skirts or early flapper dresses, cloche hats."
        )
    if year < 1960:
        return (
            "Update clothing to authentic mid-century fashion: men in tailored suits "
            "with wide lapels and fedora hats; women in full-skirted dresses with "
            "nipped waists, pearl accessories, and period-appropriate hairstyles "
            "like victory rolls or pin curls."
        )
    if year < 1980:
        return (
            "Update clothing to 1960s-70s fashion: men in slim suits or casual "
            "turtlenecks, sideburns; women in mini skirts, shift dresses, or "
            "bell-bottoms with peace-era accessories."
        )
    if year < 2000:
        return (
            "Update clothing to 1980s-90s fashion: men in power suits with shoulder pads "
            "or casual denim; women in bold colors, big hair, shoulder pads, "
            "or grunge-era flannel and jeans."
        )
    return "Keep clothing modern and contemporary."


def _build_prompt(year: int, mode: str) -> tuple[str, str]:
    """
    Build the transformation prompt based on mode.
    
    Returns (prompt, style_description).
    
    Modes:
    - clothing_only: Only change clothing, keep environment intact
    - full: Change clothing + architecture/environment
    - full_vintage: Full changes + vintage photo style
    """
    clothing = _get_clothing_prompt(year)
    era_style, style_label = _get_era_style_description(year)
    
    if mode == "clothing_only":
        prompt = (
            f"Transform this photo to look like it was taken in {year}. "
            f"Keep original buildings and environment intact with minimal alterations. "
            f"{clothing} "
            f"Maintain modern photo quality and colors - only update the people's attire."
        )
        return prompt, f"Clothing only → {year}"
    
    elif mode == "full":
        prompt = (
            f"Transform this photo to look like it was taken in {year}. "
            f"{clothing} "
            f"Update architecture and surroundings to match the {year}s era: "
            f"period-appropriate vehicles, signage, street furniture, and urban landscape. "
            f"Keep modern photo quality and natural colors."
        )
        return prompt, f"Full transformation → {year}"
    
    else:  # full_vintage
        prompt = (
            f"Transform this photo to look like it was taken in {year}. "
            f"Keep original buildings and environment intact with minimal alterations. "
            f"{clothing} "
            f"{era_style}"
        )
        return prompt, style_label


# ──────────────────────────────────────────────────────────────────────
# File Helpers
# ──────────────────────────────────────────────────────────────────────

async def _save_upload(file: UploadFile) -> str:
    """Persist the uploaded file and return a relative URL path."""
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    content = await file.read()
    filepath.write_bytes(content)
    return f"/uploads/{filename}"


def _get_disk_path(url_path: str) -> Path:
    """Convert URL path like /uploads/abc.jpg to disk path."""
    return UPLOAD_DIR / Path(url_path).name


# ──────────────────────────────────────────────────────────────────────
# GeminiGen Provider
# ──────────────────────────────────────────────────────────────────────

async def _call_geminigen(
    prompt: str, file_path: str, db: AsyncSession = None,
) -> dict:
    """Send an image-to-image generation request to GeminiGen.AI."""
    disk_path = _get_disk_path(file_path)

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

    for item in data.get("result", []):
        if str(item.get("uuid")) == str(geminigen_uuid):
            return item

    return data.get("result", [{}])[0] if data.get("result") else {}


# ──────────────────────────────────────────────────────────────────────
# KIE AI Provider
# ──────────────────────────────────────────────────────────────────────

async def _upload_to_kie(file_path: str, db: AsyncSession) -> str:
    """Upload image to KIE file storage and return the URL."""
    api_key = await get_setting(db, "KIE_API_KEY")
    disk_path = _get_disk_path(file_path)
    
    # Read file and encode to base64
    with open(disk_path, "rb") as f:
        file_content = f.read()
    base64_data = base64.b64encode(file_content).decode("utf-8")
    
    # Determine mime type
    ext = disk_path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime_type = mime_map.get(ext, "image/jpeg")
    
    # Create data URL format
    data_url = f"data:{mime_type};base64,{base64_data}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "base64Data": data_url,
        "uploadPath": "time-machine",
        "fileName": f"upload-{uuid.uuid4().hex}{ext}"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(KIE_FILE_UPLOAD_URL, headers=headers, json=payload)
    
    resp.raise_for_status()
    data = resp.json()
    
    if data.get("success") and data.get("data", {}).get("fileUrl"):
        return data["data"]["fileUrl"]
    
    raise ValueError(f"KIE file upload failed: {data}")


async def _call_kie(
    prompt: str, file_path: str, db: AsyncSession
) -> dict:
    """Send image generation request to KIE AI using nano-banana-pro model."""
    api_key = await get_setting(db, "KIE_API_KEY")
    
    # First, upload the image to KIE
    image_url = await _upload_to_kie(file_path, db)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "image_input": [image_url],
            "aspect_ratio": "1:1",
            "resolution": "1K",
            "output_format": "png"
        }
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{KIE_API_BASE}/api/v1/jobs/createTask",
            headers=headers,
            json=payload
        )
    
    resp.raise_for_status()
    data = resp.json()
    
    if data.get("code") == 200 and data.get("data", {}).get("taskId"):
        return {
            "task_id": data["data"]["taskId"],
            "status": "processing",
            "provider": "kie"
        }
    
    raise ValueError(f"KIE API error: {data.get('msg', 'Unknown error')}")


async def _poll_kie(task_id: str, db: AsyncSession) -> dict:
    """Check the status of a KIE generation task."""
    api_key = await get_setting(db, "KIE_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{KIE_API_BASE}/api/v1/jobs/getTask",
            headers=headers,
            params={"taskId": task_id}
        )
    
    resp.raise_for_status()
    data = resp.json()
    
    # KIE returns code 200 with task details
    if data.get("code") == 200:
        task_data = data.get("data", {})
        status = task_data.get("status", "processing")
        
        # Map KIE status to our status
        # KIE uses: "pending", "processing", "success", "failed"
        if status == "success":
            return {
                "status": 2,  # completed
                "generate_result": task_data.get("output", {}).get("image_url") or 
                                   task_data.get("output", {}).get("url") or
                                   (task_data.get("output", {}).get("images", [None])[0])
            }
        elif status == "failed":
            return {
                "status": 3,  # failed
                "error_message": task_data.get("error") or "Generation failed"
            }
        else:
            return {"status": 1}  # processing
    
    return {"status": 1}  # assume still processing


# ──────────────────────────────────────────────────────────────────────
# Unified Provider Interface
# ──────────────────────────────────────────────────────────────────────

async def _generate_with_provider(
    prompt: str, file_path: str, db: AsyncSession
) -> tuple[str, Optional[str], str, Optional[str]]:
    """
    Generate image using configured provider.
    
    Returns: (provider_uuid, result_url, status, error_message)
    """
    provider = await get_setting(db, "TIME_MACHINE_PROVIDER") or "geminigen"
    
    if provider == "kie":
        result = await _call_kie(prompt, file_path, db)
        return result["task_id"], None, "processing", None
    else:
        # Default to geminigen
        api_resp = await _call_geminigen(prompt, file_path, db)
        provider_uuid = str(api_resp.get("uuid") or api_resp.get("id") or "")
        
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
            return provider_uuid, result_url, "completed", None
        else:
            return provider_uuid, None, "processing", None


async def _poll_provider(
    provider_uuid: str, provider: str, db: AsyncSession
) -> dict:
    """Poll generation status for configured provider."""
    if provider == "kie":
        return await _poll_kie(provider_uuid, db)
    else:
        return await _poll_geminigen(provider_uuid, db)


# ──────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/balance", response_model=CrystalBalance)
async def get_balance(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get current Chrono-Crystal balance."""
    return CrystalBalance(chrono_crystals=current_user.chrono_crystals)


@router.get("/config", response_model=TimeMachineConfig)
async def get_config(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get current Time Machine configuration."""
    provider = await get_setting(db, "TIME_MACHINE_PROVIDER") or "geminigen"
    mode = await get_setting(db, "TIME_MACHINE_MODE") or "full_vintage"
    
    return TimeMachineConfig(
        provider=provider,
        mode=mode,
        modes=[
            {"id": "clothing_only", "name": "Только одежда", "desc": "Изменить только одежду людей под эпоху, здания и окружение остаются современными"},
            {"id": "full", "name": "Полная трансформация", "desc": "Изменить одежду + архитектуру и окружение под эпоху, сохранить современное качество фото"},
            {"id": "full_vintage", "name": "Полная + винтаж", "desc": "Полная трансформация + стиль фото эпохи (ч/б, сепия, зернистость, виньетка)"}
        ]
    )


@router.post("/generate", response_model=TimePhotoOut, status_code=status.HTTP_201_CREATED)
async def generate_time_photo(
    target_year: int = Form(..., ge=1800, le=2030),
    apply_era_style: bool = Form(True),  # Kept for backward compatibility
    mode: Optional[str] = Form(None),  # New: explicit mode selection
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Upload a photo and start a Time-Machine transformation.

    Costs 1 Chrono-Crystal. The generation runs asynchronously —
    poll ``/check/{photo_id}`` to track progress.
    
    Modes:
    - clothing_only: Only update clothing
    - full: Update clothing + architecture
    - full_vintage: Full update + vintage photo style
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

    # 4. Determine mode
    if mode is None:
        # Use global setting or legacy apply_era_style flag
        mode = await get_setting(db, "TIME_MACHINE_MODE") or "full_vintage"
        if not apply_era_style:
            mode = "full"  # Legacy: apply_era_style=False means no vintage style
    
    # 5. Build prompt
    prompt, style_desc = _build_prompt(target_year, mode)

    # 6. Get provider
    provider = await get_setting(db, "TIME_MACHINE_PROVIDER") or "geminigen"

    # 7. Call provider
    provider_uuid = None
    result_url = None
    photo_status = "processing"
    error_message = None

    try:
        provider_uuid, result_url, photo_status, error_message = await _generate_with_provider(
            prompt, original_url, db
        )
    except httpx.HTTPStatusError as exc:
        photo_status = "failed"
        error_message = f"API error: {exc.response.status_code} — {exc.response.text[:300]}"
        current_user.chrono_crystals += 1  # Refund on API error
    except Exception as exc:
        photo_status = "failed"
        error_message = f"API request failed: {exc}"
        current_user.chrono_crystals += 1  # Refund on error

    # 8. Save TimePhoto record
    time_photo = TimePhoto(
        user_id=current_user.id,
        original_image_url=original_url,
        result_image_url=result_url,
        target_year=target_year,
        apply_era_style=(mode == "full_vintage"),
        style_applied=style_desc,
        prompt_used=prompt,
        geminigen_uuid=provider_uuid,  # Stores provider task ID
        provider=provider,
        transformation_mode=mode,
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
    total_q = await db.execute(
        select(sa_func.count()).select_from(TimePhoto).where(TimePhoto.user_id == current_user.id)
    )
    total = total_q.scalar() or 0
    pages = ceil(total / per_page) if per_page else 1

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
    """Poll provider for the status of a pending generation."""
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
            detail="Нет ID для проверки статуса генерации",
        )

    # Determine provider (use stored or current setting)
    provider = getattr(photo, 'provider', None) or await get_setting(db, "TIME_MACHINE_PROVIDER") or "geminigen"

    try:
        poll_resp = await _poll_provider(photo.geminigen_uuid, provider, db)
    except httpx.HTTPStatusError as exc:
        photo.status = "failed"
        photo.error_message = f"Poll error: {exc.response.status_code}"
        current_user.chrono_crystals += 1
        await db.commit()
        await db.refresh(photo)
        return photo
    except Exception as exc:
        photo.status = "failed"
        photo.error_message = f"Poll request failed: {exc}"
        current_user.chrono_crystals += 1
        await db.commit()
        await db.refresh(photo)
        return photo

    api_status = poll_resp.get("status")

    # Status mapping: 2 = completed, 3 = failed, 1 = processing
    if api_status == 2:
        result_url = (
            poll_resp.get("generate_result")
            or poll_resp.get("thumbnail_url")
            or poll_resp.get("last_frame_url")
        )
        if result_url:
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
        current_user.chrono_crystals += 1
    # else still processing (status=1) — keep status as-is

    await db.commit()
    await db.refresh(photo)
    return photo
