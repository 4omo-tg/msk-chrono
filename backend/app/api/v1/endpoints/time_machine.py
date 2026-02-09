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
import hmac
import hashlib
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
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

def _get_full_era_prompt(year: int) -> tuple[str, str]:
    """
    Return (full_prompt, style_label) for the target year.
    These are comprehensive prompts for full_vintage mode with Russian/Moscow context.
    """
    if year < 1850:
        return (
            f"Transform this photo to look like it was captured in {year}. "
            "Moderately adapt the environment to early 19th-century Imperial Russia: "
            "replace modern elements with dirt/cobblestone roads, horse-drawn carriages "
            "and sedan chairs, wooden merchant stalls with Cyrillic signage, wrought-iron "
            "lanterns, and period-appropriate details like wooden fences and hand-painted "
            "shop signs. Preserve architectural silhouette but enhance with Empire-style "
            "details: classical cornices, columns, and wooden window shutters. Replace "
            "clothing with authentic 1800s fashion: men in tailcoats with high collars, "
            "waistcoats, breeches, tricorne or bicorne hats, and leather boots; women in "
            "high-waisted Empire silhouette dresses, fichu shawls, bonnets with ribbons, "
            "and delicate gloves. Apply early 19th-century artistic style: soft sepia-toned "
            "palette mimicking hand-tinted engravings, subtle paper texture, gentle brushstroke "
            "effect, faded edges, and characteristic tonal range of aquatint prints from the era.",
            "Гравюра начала XIX века"
        )
    if year < 1900:
        return (
            f"Transform this photo to look like it was taken in {year}. "
            "Moderately adapt the environment to mid-19th century Imperial Russia: "
            "replace modern elements with cobblestone streets, horse-drawn carriages, "
            "gas lanterns, wooden merchant stalls, and period-appropriate shop signs "
            "with Cyrillic lettering; preserve architectural silhouette but add historical "
            "details like wrought-iron balconies and wooden shutters. Replace clothing "
            "with authentic 1850s fashion: men in tailcoats with standing collars, top hats, "
            "and leather boots; women in crinoline skirts, corseted bodices, bonnets, and "
            "lace shawls. Apply daguerreotype/early photographic style: sepia-toned palette, "
            "subtle silver nitrate grain, soft focus, vignette edges, and characteristic "
            "tonal range of 1850s wet-plate collodion process.",
            "Дагеротип XIX века"
        )
    if year < 1940:
        return (
            f"Transform this photo to look like it was taken in {year}. "
            "Moderately adapt the environment to turn-of-the-century Imperial Russia: "
            "replace modern elements with cobblestone streets, horse-drawn carriages and "
            "early automobiles, gas lanterns, wooden merchant stalls with Cyrillic signage, "
            "wrought-iron street lamps, and period shop windows with vintage advertisements. "
            "Preserve architectural silhouette but enhance with historical details like "
            "decorative cornices and wooden window frames. Replace clothing with authentic "
            "1900s fashion: men in three-piece suits, waistcoats, bowler hats or fedoras, "
            "leather boots; women in long tailored dresses with high collars, leg-of-mutton "
            "sleeves, wide-brimmed hats with ribbons, and lace gloves. Apply early 20th-century "
            "photographic style: soft sepia or toned black-and-white palette, fine film grain, "
            "gentle vignette, moderate contrast, and characteristic tonal range of 1900s "
            "dry-plate gelatin photography.",
            "Фото начала XX века"
        )
    if year < 1970:
        return (
            f"Transform this photo to look like it was taken in {year}. "
            "Moderately adapt the environment to post-war Soviet Moscow: replace modern "
            "elements with cobblestone/asphalt streets, trolleybuses and GAZ-M20 Pobeda cars, "
            "wooden benches, vintage 'Soyuzpechat' kiosks, Cyrillic shop signs with period "
            "typography, and subtle propaganda posters on walls. Preserve architectural "
            "silhouette but enhance with 1950s details like wrought-iron railings and wooden "
            "window frames. Replace clothing with authentic late-Stalin era fashion: men in "
            "wool suits, peaked caps or fedoras, buttoned jackets; women in A-line dresses "
            "with modest prints, headscarves tied under the chin, and low-heeled shoes. "
            "Apply 1950s Soviet photographic style: desaturated black-and-white or cool-toned "
            "sepia palette, fine film grain, soft contrast, gentle vignette, and characteristic "
            "tonal range of domestic Svema film stock.",
            "Советское фото 1950-х"
        )
    if year < 2000:
        return (
            f"Transform this photo to look like it was taken in {year}. "
            "Moderately adapt the environment to late Soviet/early post-Soviet Moscow: "
            "add period details like Lada and Moskvitch cars, metal kiosks, hand-painted "
            "Cyrillic signage, and Soviet-era bus stops. Preserve architectural silhouette "
            "but add details like TV antennas on roofs. Replace clothing with authentic "
            "1980s fashion: men in synthetic jackets, wide-collar shirts; women in bright "
            "printed dresses, permed hair. Apply retro film photography style with warm tones, "
            "visible film grain, slightly faded colors, and color palette typical of 1980s "
            "Soviet Tasma film stock.",
            "Советское фото 1980-х"
        )
    if year < 2010:
        return (
            f"Transform this photo to look like it was taken in {year}. "
            "Moderately adapt the environment to turn-of-the-millennium Moscow: replace "
            "modern elements with early 2000s details — Lada Samara and VAZ-2109 cars, "
            "neon-lit kiosks with 'GSM' signs, early mobile phone advertisements, plastic "
            "café chairs on sidewalks, and Cyrillic signage with Y2K-era typography. Preserve "
            "architectural silhouette but add period details like satellite dishes on balconies "
            "and early LED displays. Replace clothing with authentic late 1990s/early 2000s "
            "fashion: men in oversized denim jackets, cargo pants, logo t-shirts, and baseball "
            "caps; women in low-rise jeans, crop tops, velour tracksuits, platform shoes, and "
            "butterfly clips in hair. Apply early digital photography style: slightly "
            "oversaturated colors, subtle JPEG compression artifacts, soft focus, mild "
            "chromatic aberration, and characteristic color cast of early 2000s compact "
            "digital cameras.",
            "Цифровое фото 2000-х"
        )
    if year > 2050:
        return (
            f"Transform this photo to look like it was captured in {year}. "
            "Moderately adapt the environment to near-future Moscow: integrate subtle "
            "cyberpunk elements — holographic Cyrillic signage floating above streets, "
            "sleek autonomous electric vehicles gliding on smart roads, augmented reality "
            "wayfinding projections on building facades, vertical greenery on historic "
            "structures, and minimalist transit pods. Preserve architectural silhouette "
            "of Moscow landmarks but enhance with sustainable tech: solar-glass cladding, "
            "kinetic energy pavement, and discreet drone ports. Replace clothing with "
            "futuristic fashion: adaptive smart fabrics with subtle luminescent threads, "
            "minimalist silhouettes with magnetic closures, AR glasses integrated into "
            "lightweight frames, and biometric wearables. Apply futuristic visual aesthetic: "
            "crisp neo-noir palette with electric cyan/magenta accents against desaturated "
            "urban tones, clean volumetric lighting, subtle lens flare from holograms, "
            "fine digital grain, and characteristic render quality of next-gen light-field "
            "photography.",
            "Киберпанк будущего"
        )
    # Default modern
    return (
        f"Transform this photo to look like it was taken in {year}. "
        "Keep modern environment and clothing. Apply contemporary digital photography style "
        "with natural colors and sharp details.",
        "Современное фото"
    )


def _get_clothing_prompt(year: int) -> str:
    """Return clothing/fashion description for the target year (Russian context)."""
    if year < 1850:
        return (
            "Update clothing to early 19th century Imperial Russian fashion: men in tailcoats "
            "with high collars, waistcoats, breeches, tricorne or bicorne hats, and leather boots; "
            "women in high-waisted Empire silhouette dresses, fichu shawls, bonnets with ribbons, "
            "and delicate gloves."
        )
    if year < 1900:
        return (
            "Update clothing to mid-19th century Imperial Russian fashion: men in tailcoats "
            "with standing collars, top hats, and leather boots; women in crinoline skirts, "
            "corseted bodices, bonnets, and lace shawls."
        )
    if year < 1940:
        return (
            "Update clothing to early 20th century Russian fashion: men in three-piece suits, "
            "waistcoats, bowler hats or fedoras, leather boots; women in long tailored dresses "
            "with high collars, leg-of-mutton sleeves, wide-brimmed hats with ribbons, and lace gloves."
        )
    if year < 1970:
        return (
            "Update clothing to Soviet 1950s fashion: men in wool suits, peaked caps or fedoras, "
            "buttoned jackets; women in A-line dresses with modest prints, headscarves tied "
            "under the chin, and low-heeled shoes."
        )
    if year < 2000:
        return (
            "Update clothing to late Soviet 1980s fashion: men in synthetic jackets, "
            "wide-collar shirts, flat caps; women in bright printed dresses, permed hair, "
            "and practical low-heeled shoes."
        )
    if year < 2010:
        return (
            "Update clothing to early 2000s post-Soviet fashion: men in oversized denim jackets, "
            "cargo pants, logo t-shirts, and baseball caps; women in low-rise jeans, crop tops, "
            "velour tracksuits, platform shoes, and butterfly clips in hair."
        )
    if year > 2050:
        return (
            "Update clothing to futuristic fashion: adaptive smart fabrics with subtle luminescent "
            "threads, minimalist silhouettes with magnetic closures, AR glasses integrated into "
            "lightweight frames, and biometric wearables."
        )
    return "Keep clothing modern and contemporary."


def _build_prompt(year: int, mode: str) -> tuple[str, str]:
    """
    Build the transformation prompt based on mode.
    
    Returns (prompt, style_description).
    
    Modes:
    - clothing_only: Only change clothing, keep environment intact
    - full: Change clothing + architecture/environment (modern photo quality)
    - full_vintage: Full changes + vintage photo style (comprehensive prompt)
    """
    clothing = _get_clothing_prompt(year)
    
    if mode == "clothing_only":
        prompt = (
            f"Transform this photo to look like it was taken in {year}. "
            f"Keep original buildings and environment completely intact with no alterations. "
            f"{clothing} "
            f"Maintain modern photo quality and colors - only update the people's attire."
        )
        return prompt, f"Только одежда → {year}"
    
    elif mode == "full":
        prompt = (
            f"Transform this photo to look like it was taken in {year}. "
            f"{clothing} "
            f"Moderately update environment to match {year}s era: period-appropriate vehicles, "
            f"signage with Cyrillic lettering, street furniture, and urban landscape details. "
            f"Preserve architectural silhouette but add historical details. "
            f"Keep modern photo quality with natural colors and sharp details."
        )
        return prompt, f"Полная трансформация → {year}"
    
    else:  # full_vintage - use comprehensive era-specific prompt
        prompt, style_label = _get_full_era_prompt(year)
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
    
    # API returns downloadUrl, not fileUrl
    if data.get("success") or data.get("code") == 200:
        file_data = data.get("data", {})
        url = file_data.get("downloadUrl") or file_data.get("fileUrl")
        if url:
            return url
    
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
    
    # Build callback URL - KIE will POST results here
    # Note: In production, this should be your public URL
    callback_url = "https://cache-rain.exe.xyz:8000/api/v1/time-machine/kie-callback"
    
    payload = {
        "model": "nano-banana-pro",
        "callBackUrl": callback_url,
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
    """
    Check the status of a KIE generation task.
    
    KIE API uses webhooks for results - there's no polling endpoint.
    The webhook callback updates the TimePhoto record directly.
    This function just checks if the record was updated by the webhook.
    """
    # Check if the photo was already updated by webhook
    result = await db.execute(
        select(TimePhoto).where(TimePhoto.geminigen_uuid == task_id)
    )
    photo = result.scalars().first()
    
    if photo:
        if photo.status == "completed" and photo.result_image_url:
            return {
                "status": 2,  # completed
                "generate_result": photo.result_image_url
            }
        elif photo.status == "failed":
            return {
                "status": 3,  # failed
                "error_message": photo.error_message or "Generation failed"
            }
    
    # Still waiting for webhook callback
    return {"status": 1}  # processing


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
    target_year: int = Form(..., ge=1800, le=2100),
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


# ──────────────────────────────────────────────────────────────────────
# KIE Webhook Callback
# ──────────────────────────────────────────────────────────────────────

@router.post("/kie-callback", include_in_schema=False)
async def kie_webhook_callback(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Webhook endpoint for KIE AI to send generation results.
    KIE will POST here when generation is complete.
    Verifies HMAC signature for security.
    """
    # Get raw body for signature verification
    raw_body = await request.body()
    
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Extract task info
    task_id = body.get("taskId") or body.get("data", {}).get("task_id")
    
    # Verify HMAC signature if present
    timestamp = request.headers.get("X-Webhook-Timestamp")
    received_signature = request.headers.get("X-Webhook-Signature")
    
    if timestamp and received_signature:
        # Get HMAC key from settings
        hmac_key = await get_setting(db, "KIE_WEBHOOK_HMAC_KEY")
        if hmac_key:
            # Generate expected signature: base64(HMAC-SHA256(taskId + "." + timestamp, key))
            data_to_sign = f"{task_id}.{timestamp}"
            expected_signature = base64.b64encode(
                hmac.new(
                    hmac_key.encode(),
                    data_to_sign.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()
            
            # Constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(expected_signature, received_signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
    code = body.get("code", 0)
    data = body.get("data", {})
    
    if not task_id:
        raise HTTPException(status_code=400, detail="Missing taskId")
    
    # Find the photo by geminigen_uuid (which stores KIE task_id)
    result = await db.execute(
        select(TimePhoto).where(TimePhoto.geminigen_uuid == task_id)
    )
    photo = result.scalars().first()
    
    if not photo:
        # Task not found - might be from another system
        return {"status": "ignored", "reason": "task not found"}
    
    # Already processed
    if photo.status in ("completed", "failed"):
        return {"status": "already_processed"}
    
    # Process result
    if code == 200:
        # Success - extract result URL
        output = data.get("output", {})
        result_url = None
        
        if isinstance(output, dict):
            result_url = (
                output.get("image_url") or
                output.get("url") or
                output.get("image") or
                (output.get("images", [None])[0] if output.get("images") else None)
            )
        elif isinstance(output, list) and len(output) > 0:
            first = output[0]
            result_url = first if isinstance(first, str) else first.get("url") if isinstance(first, dict) else None
        elif isinstance(output, str):
            result_url = output
        
        # Also check top-level data fields
        if not result_url:
            result_url = (
                data.get("result") or
                data.get("image_url") or
                data.get("url") or
                data.get("output_url")
            )
        
        if result_url:
            photo.result_image_url = result_url
            photo.status = "completed"
            photo.completed_at = datetime.utcnow()
        else:
            photo.status = "failed"
            photo.error_message = "No result URL in callback"
            # Refund crystal
            user_result = await db.execute(
                select(models.User).where(models.User.id == photo.user_id)
            )
            user = user_result.scalars().first()
            if user:
                user.chrono_crystals += 1
    else:
        # Failed
        photo.status = "failed"
        photo.error_message = data.get("error") or data.get("message") or body.get("msg") or "Generation failed"
        # Refund crystal
        user_result = await db.execute(
            select(models.User).where(models.User.id == photo.user_id)
        )
        user = user_result.scalars().first()
        if user:
            user.chrono_crystals += 1
    
    await db.commit()
    
    return {"status": "processed", "task_id": task_id}
