from typing import Any
import math
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import models, schemas
from app.api import deps

router = APIRouter()

AI_PROXY_URL = "http://127.0.0.1:3264"
AI_PROXY_TOKEN = "mein_key"


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

@router.post("/verify-poi", response_model=schemas.VerificationResponse)
async def verify_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    file: UploadFile = File(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    poi_id: int = Form(...),
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
        # If neither geo nor file provided
        raise HTTPException(status_code=400, detail="Must provide either Geolocation or Photo.")
        
    # 3. AI Check (if provided)
    if file is not None:
        async with httpx.AsyncClient(timeout=30.0, headers={"Authorization": f"Bearer {AI_PROXY_TOKEN}"}) as client:
            # a. Upload image
            image_url = ""
            try:
                # Re-read file to bytes
                content = await file.read()
                
                # Prepare multipart upload
                files = {"file": (file.filename, content, file.content_type)}
                
                # Note: The proxy might expect specific field name 'file'
                upload_res = await client.post(f"{AI_PROXY_URL}/api/files/upload", files=files)
                upload_res.raise_for_status()
                response_json = upload_res.json()
                if not response_json:
                    raise Exception(f"Empty response from proxy: {upload_res.status_code}")
                
                image_url = response_json.get("imageUrl")
                if not image_url:
                    image_url = response_json.get("file", {}).get("url")
                
                if not image_url:
                     raise Exception(f"No imageUrl in response: {response_json}")
                     
            except httpx.HTTPError as he:
                print(f"Upload HTTP error: {he}")
                if hasattr(he, 'response') and he.response is not None:
                    print(f"Response body: {he.response.text}")
                    return schemas.VerificationResponse(verified=False, message=f"Ошибка прокси: {he.response.status_code} {he.response.text[:100]}")
                return schemas.VerificationResponse(verified=False, message=f"Ошибка сети: {str(he)}")
            except Exception as e:
                 import traceback
                 traceback.print_exc()
                 print(f"Upload failed: {type(e).__name__}: {str(e)}")
                 return schemas.VerificationResponse(verified=False, message=f"Ошибка загрузки фото: {type(e).__name__} {str(e)}")

            # b. Chat completion
            try:
                system_prompt = "Ты - гид по Москве. Твоя задача - проверить, соответствует ли фото пользователя описанию достопримечательности. Отвечай только 'YES' если похоже, или 'NO' если это что-то другое. Затем кратко объясни почему."
                user_prompt = f"Посмотри на это фото. Это похоже на '{poi.title}'? Описание: {poi.description}. На фото должно быть именно это место."
                
                # Use Proxy Native format
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                payload_native = {
                     "message": [
                        {"type": "text", "text": full_prompt},
                        {"type": "image", "image": image_url}
                     ],
                     "model": "qwen2.5-vl-32b-instruct"
                }
                
                chat_res = await client.post(f"{AI_PROXY_URL}/api/chat", json=payload_native)
                chat_res.raise_for_status()
                
                data = chat_res.json()
                # print(f"DEBUG AI RESP: {data}")
                content = data.get("message")
                if not content and "choices" in data:
                     content = data["choices"][0]["message"]["content"]
                
                verified = "YES" in content.upper() or "ДА" in content.upper()
                
                return schemas.VerificationResponse(
                    verified=verified,
                    message=content
                )

            except Exception as e:
                print(f"AI Check failed: {e}")
                return schemas.VerificationResponse(verified=False, message="Сервис проверки фото временно недоступен")
    
    # If only Geo Check was done and passed
    return schemas.VerificationResponse(
        verified=True,
        message="Местоположение подтверждено!"
    )
