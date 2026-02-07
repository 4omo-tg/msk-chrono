from typing import Any, List
import math
import base64
import httpx
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()

# Random gestures for liveness verification
GESTURES = [
    {"id": "thumbs_up", "name": "Большой палец вверх 👍", "description": "Покажите большой палец вверх рядом с достопримечательностью"},
    {"id": "peace", "name": "Знак мира ✌️", "description": "Покажите знак мира (два пальца) рядом с достопримечательностью"},
    {"id": "ok", "name": "Знак OK 👌", "description": "Покажите знак OK рядом с достопримечательностью"},
    {"id": "wave", "name": "Помашите рукой 👋", "description": "Покажите раскрытую ладонь рядом с достопримечательностью"},
]


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3 # metres
    phi1 = lat1 * math.pi/180
    phi2 = lat2 * math.pi/180
    delta_phi = (lat2-lat1) * math.pi/180
    delta_lam = (lon2-lon1) * math.pi/180
    
    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lam/2) * math.sin(delta_lam/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def get_random_gesture() -> dict:
    """Get a random gesture for liveness verification."""
    import random
    return random.choice(GESTURES)


@router.get("/gesture")
async def get_verification_gesture(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> dict:
    """Get a random gesture that user must show in photo for liveness check."""
    gesture = get_random_gesture()
    return {
        "gesture_id": gesture["id"],
        "gesture_name": gesture["name"],
        "gesture_description": gesture["description"]
    }


async def upload_image_to_qwen(image_content: bytes, content_type: str) -> str:
    """Upload image to Qwen API and get URL for use in requests."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        files = {
            'file': ('image.jpg', image_content, content_type)
        }
        
        upload_res = await client.post(
            f"{settings.AI_API_BASE_URL}/files/upload",
            files=files
        )
        upload_res.raise_for_status()
        data = upload_res.json()
        # API returns URL in file.url field
        url = data.get("imageUrl") or data.get("file", {}).get("url")
        print(f"Uploaded image URL: {url[:100] if url else 'None'}...")
        return url


@router.post("/verify-poi", response_model=schemas.VerificationResponse)
async def verify_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    file: UploadFile = File(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    poi_id: int = Form(...),
    gesture_id: str = Form(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Verify check-in at a POI using Geolocation and AI Photo Analysis.
    """
    # 1. Get POI
    poi = await db.get(models.PointOfInterest, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    # 2. Geo Check (if provided)
    if latitude is not None and longitude is not None:
        distance = calculate_distance(latitude, longitude, poi.latitude, poi.longitude)
        if distance > 200: 
            return schemas.VerificationResponse(
                verified=False,
                message=f"Вы находитесь слишком далеко ({int(distance)}м). Подойдите ближе к точке."
            )
    elif file is None:
        raise HTTPException(status_code=400, detail="Must provide either Geolocation or Photo.")
        
    # 3. AI Check (if photo provided)
    if file is not None:
        if not gesture_id:
            raise HTTPException(status_code=400, detail="Gesture is required for photo verification")
        
        gesture_info = next((g for g in GESTURES if g["id"] == gesture_id), None)
        if not gesture_info:
            raise HTTPException(status_code=400, detail="Invalid gesture")
            
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # Read and upload user's photo
                content = await file.read()
                content_type = file.content_type or "image/jpeg"
                
                # Upload image to get URL
                try:
                    user_image_url = await upload_image_to_qwen(content, content_type)
                except Exception as upload_err:
                    print(f"Failed to upload user image: {upload_err}")
                    return schemas.VerificationResponse(
                        verified=False,
                        message="Не удалось загрузить фото. Попробуйте ещё раз."
                    )
                
                # Build prompt text
                prompt = f"""Ты - система верификации посещения достопримечательностей Москвы.

Проверь фото пользователя:
- Название места: {poi.title}
- Описание: {poi.description or 'не указано'}
- Требуемый жест: {gesture_info['name']} ({gesture_info['description']})

Проверь:
1. Видна ли достопримечательность "{poi.title}" на фото?
2. Виден ли требуемый жест {gesture_info['name']} на фото?

Отвечай строго в формате:
РЕЗУЛЬТАТ: YES или NO
МЕСТО: да/нет - видна ли достопримечательность и почему
ЖЕСТ: да/нет - виден ли требуемый жест
ПРИЧИНА: если NO - подробно объясни что не так и что нужно исправить"""
                
                # Use native /api/chat format with image
                payload = {
                    "message": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": user_image_url}
                    ],
                    "model": settings.AI_MODEL
                }
                
                chat_res = await client.post(
                    f"{settings.AI_API_BASE_URL}/chat",
                    json=payload
                )
                chat_res.raise_for_status()
                
                data = chat_res.json()
                # Native format returns 'message' field
                response_content = data.get("message", "")
                if not response_content and "choices" in data:
                    response_content = data["choices"][0]["message"]["content"]
                
                print(f"AI Response: {response_content}")  # Debug log
                
                # Parse response
                response_upper = response_content.upper()
                verified = "РЕЗУЛЬТАТ: YES" in response_upper or "РЕЗУЛЬТАТ:YES" in response_upper or ("YES" in response_upper and "NO" not in response_upper.split("\n")[0])
                
                # Extract detailed info
                lines = response_content.split("\n")
                place_ok = None
                gesture_ok = None
                reason = ""
                place_comment = ""
                gesture_comment = ""
                
                for line in lines:
                    line_upper = line.upper().strip()
                    if line_upper.startswith("МЕСТО:") or "МЕСТО:" in line_upper:
                        value = line.split(":", 1)[-1].strip()
                        place_ok = value.upper().startswith("ДА") or "YES" in value.upper()
                        place_comment = value
                    elif line_upper.startswith("ЖЕСТ:") or "ЖЕСТ:" in line_upper:
                        value = line.split(":", 1)[-1].strip()
                        gesture_ok = value.upper().startswith("ДА") or "YES" in value.upper()
                        gesture_comment = value
                    elif line_upper.startswith("ПРИЧИНА:") or "ПРИЧИНА:" in line_upper:
                        reason = line.split(":", 1)[-1].strip()
                
                print(f"Parsed - place_ok: {place_ok}, gesture_ok: {gesture_ok}, reason: {reason}")
                
                # Build user-friendly message
                if verified:
                    message = "Верификация успешна! Место и жест подтверждены."
                else:
                    # Build detailed rejection reason
                    issues = []
                    if place_ok == False:
                        issues.append(f"❌ Достопримечательность не распознана")
                    elif place_ok == True:
                        issues.append(f"✅ Достопримечательность определена")
                    
                    if gesture_ok == False:
                        issues.append(f"❌ Жест '{gesture_info['name']}' не обнаружен")
                    elif gesture_ok == True:
                        issues.append(f"✅ Жест обнаружен")
                    
                    if reason:
                        issues.append(f"\n📝 {reason}")
                    
                    if issues:
                        message = "\n".join(issues)
                    else:
                        # Fallback - show raw AI response
                        message = response_content[:300] if len(response_content) > 300 else response_content
                
                return schemas.VerificationResponse(
                    verified=verified,
                    message=message
                )

            except httpx.HTTPError as he:
                print(f"AI HTTP error: {he}")
                if hasattr(he, 'response') and he.response is not None:
                    print(f"Response body: {he.response.text}")
                return schemas.VerificationResponse(verified=False, message="Сервис проверки фото временно недоступен")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"AI Check failed: {type(e).__name__}: {e}")
                return schemas.VerificationResponse(verified=False, message="Сервис проверки фото временно недоступен")
    
    # If only Geo Check was done and passed
    return schemas.VerificationResponse(
        verified=True,
        message="Местоположение подтверждено!"
    )
