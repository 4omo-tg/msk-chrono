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


async def upload_image_to_qwen(client: httpx.AsyncClient, image_content: bytes, content_type: str) -> str:
    """Upload image to Qwen API and get URL for use in requests."""
    import io
    
    # Create multipart form data
    files = {
        'file': ('image.jpg', image_content, content_type)
    }
    
    upload_res = await client.post(
        f"{settings.AI_API_BASE_URL}/files/upload",
        files=files
    )
    upload_res.raise_for_status()
    data = upload_res.json()
    return data.get("imageUrl")


async def load_reference_images(poi: models.PointOfInterest) -> List[str]:
    """Load reference images for POI and return as base64 data URLs."""
    reference_urls = []
    
    # Get modern images as references
    images_to_check = []
    if poi.modern_images:
        images_to_check.extend(poi.modern_images[:2])  # Max 2 reference images
    if poi.modern_image_url and poi.modern_image_url not in images_to_check:
        images_to_check.append(poi.modern_image_url)
    
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
    
    for img_url in images_to_check[:2]:  # Limit to 2 references
        if img_url:
            # Handle local files
            if img_url.startswith("/uploads/"):
                filename = img_url.replace("/uploads/", "")
                filepath = os.path.join(uploads_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        content = f.read()
                    ext = os.path.splitext(filename)[1].lower()
                    mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png" if ext == ".png" else "image/jpeg"
                    base64_image = base64.b64encode(content).decode('utf-8')
                    reference_urls.append(f"data:{mime};base64,{base64_image}")
            elif img_url.startswith("http"):
                # External URLs - pass as-is
                reference_urls.append(img_url)
    
    return reference_urls


@router.post("/verify-poi", response_model=schemas.VerificationResponse)
async def verify_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    file: UploadFile = File(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    poi_id: int = Form(...),
    gesture_id: str = Form(None),  # Required gesture for liveness check
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Verify check-in at a POI using Geolocation and AI Photo Analysis.
    For photo verification, user must show a specific gesture (liveness check).
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
        # If neither geo nor file provided
        raise HTTPException(status_code=400, detail="Must provide either Geolocation or Photo.")
        
    # 3. AI Check (if provided)
    if file is not None:
        # Validate gesture is provided for photo verification
        if not gesture_id:
            raise HTTPException(status_code=400, detail="Gesture is required for photo verification")
        
        # Find gesture info
        gesture_info = next((g for g in GESTURES if g["id"] == gesture_id), None)
        if not gesture_info:
            raise HTTPException(status_code=400, detail="Invalid gesture")
            
        headers = {"Content-Type": "application/json"}
        if settings.AI_API_KEY:
            headers["Authorization"] = f"Bearer {settings.AI_API_KEY}"
            
        async with httpx.AsyncClient(timeout=120.0, headers=headers) as client:
            try:
                # Read user's photo
                content = await file.read()
                content_type = file.content_type or "image/jpeg"
                
                # Upload user's photo to get URL
                try:
                    user_image_url = await upload_image_to_qwen(
                        httpx.AsyncClient(timeout=60.0),
                        content, 
                        content_type
                    )
                except Exception as upload_err:
                    print(f"Failed to upload user image: {upload_err}")
                    # Fallback to base64
                    base64_image = base64.b64encode(content).decode('utf-8')
                    user_image_url = f"data:{content_type};base64,{base64_image}"
                
                # Load reference images
                reference_urls = await load_reference_images(poi)
                
                # Build system prompt
                system_prompt = """Ты - система верификации посещения достопримечательностей Москвы. 
Твоя задача - проверить:
1. Соответствует ли фото пользователя указанной достопримечательности
2. Показывает ли пользователь требуемый жест на фото (для подтверждения, что фото сделано в реальном времени)

Важно: жест должен быть виден на фото, но не должен полностью закрывать достопримечательность.

Отвечай строго в формате:
РЕЗУЛЬТАТ: YES или NO
МЕСТО: краткое описание, совпадает ли место
ЖЕСТ: виден ли требуемый жест
КОММЕНТАРИЙ: краткое пояснение"""
                
                # Build message content with images
                message_content = []
                
                # Add reference images if available
                if reference_urls:
                    message_content.append({
                        "type": "text",
                        "text": f"РЕФЕРЕНСНЫЕ ФОТО достопримечательности '{poi.title}':"
                    })
                    for ref_url in reference_urls:
                        message_content.append({
                            "type": "image",
                            "image": ref_url
                        })
                
                # Add user's photo and task
                message_content.append({
                    "type": "text",
                    "text": f"""\n\nФОТО ПОЛЬЗОВАТЕЛЯ для проверки:"""
                })
                message_content.append({
                    "type": "image",
                    "image": user_image_url
                })
                message_content.append({
                    "type": "text",
                    "text": f"""\n\nЗАДАНИЕ:
- Название места: {poi.title}
- Описание: {poi.description or 'не указано'}
- Требуемый жест: {gesture_info['name']} ({gesture_info['description']})

Проверь, что на фото пользователя:
1. Видна достопримечательность "{poi.title}" (сравни с референсами если они есть)
2. Виден требуемый жест: {gesture_info['name']}

Ответь в указанном формате."""
                })
                
                # Request to Qwen API
                payload = {
                    "model": settings.AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message_content}
                    ]
                }
                
                chat_res = await client.post(
                    f"{settings.AI_API_BASE_URL}/chat/completions",
                    json=payload
                )
                chat_res.raise_for_status()
                
                data = chat_res.json()
                response_content = data["choices"][0]["message"]["content"]
                
                # Parse response
                response_upper = response_content.upper()
                verified = "РЕЗУЛЬТАТ: YES" in response_upper or "РЕЗУЛЬТАТ:YES" in response_upper
                
                # Extract comment for user-friendly message
                lines = response_content.split("\n")
                comment = ""
                for line in lines:
                    if "КОММЕНТАРИЙ:" in line.upper():
                        comment = line.split(":", 1)[-1].strip()
                        break
                
                if not comment:
                    comment = response_content
                
                return schemas.VerificationResponse(
                    verified=verified,
                    message=comment if comment else ("Верификация успешна!" if verified else "Верификация не пройдена")
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
