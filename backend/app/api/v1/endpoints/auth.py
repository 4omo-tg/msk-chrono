from datetime import timedelta
from typing import Any, Optional
import hashlib
import hmac
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app import models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings

router = APIRouter()


class TelegramCodeAuth(BaseModel):
    code: str


class TelegramWidgetAuth(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


def verify_telegram_hash(data: TelegramWidgetAuth) -> bool:
    """Verify Telegram Login Widget hash"""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    
    # Check if auth_date is not too old (24 hours)
    if time.time() - data.auth_date > 86400:
        return False
    
    # Build data-check-string
    check_dict = {
        'auth_date': str(data.auth_date),
        'first_name': data.first_name,
        'id': str(data.id),
    }
    if data.last_name:
        check_dict['last_name'] = data.last_name
    if data.username:
        check_dict['username'] = data.username
    if data.photo_url:
        check_dict['photo_url'] = data.photo_url
    
    # Sort alphabetically and join
    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(check_dict.items()))
    
    # Secret key is SHA256 of bot token
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    
    # Calculate HMAC-SHA256
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == data.hash


@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Find user by username (or email if we want to support both)
    # Assuming username field in DB is unique
    result = await db.execute(select(models.User).where(models.User.username == form_data.username))
    user = result.scalars().first()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=schemas.User)
async def register(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    # Check if user exists
    result = await db.execute(select(models.User).where(models.User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    result = await db.execute(select(models.User).where(models.User.username == user_in.username))
    user = result.scalars().first()
    if user:
        raise HTTPException(
             status_code=400,
             detail="The user with this username already exists.",
        )

    user = models.User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=security.get_password_hash(user_in.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/telegram/code", response_model=schemas.Token)
async def telegram_code_auth(
    *,
    db: AsyncSession = Depends(deps.get_db),
    auth_data: TelegramCodeAuth,
) -> Any:
    """
    Authenticate via Telegram bot code.
    Creates a new user if not exists.
    """
    from sqlalchemy import text
    
    # Get code from database
    result = await db.execute(
        text("""
            DELETE FROM telegram_auth_codes 
            WHERE code = :code AND created_at > NOW() - INTERVAL '10 minutes'
            RETURNING telegram_id, telegram_username, telegram_first_name, telegram_photo_url
        """),
        {"code": auth_data.code.strip()}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=400,
            detail="Неверный или истекший код"
        )
    
    await db.commit()
    
    code_data = {
        'telegram_id': row[0],
        'username': row[1],
        'first_name': row[2],
        'photo_url': row[3],
    }
    
    telegram_id = code_data['telegram_id']
    
    # Find or create user
    result = await db.execute(
        select(models.User).where(models.User.telegram_id == telegram_id)
    )
    user = result.scalars().first()
    
    if not user:
        # Create new user
        username = code_data['username'] or f"tg_{telegram_id}"
        
        # Check if username exists
        result = await db.execute(
            select(models.User).where(models.User.username == username)
        )
        existing = result.scalars().first()
        if existing:
            # Add random suffix if username taken
            import secrets
            username = f"{username}_{secrets.token_hex(3)}"
        
        user = models.User(
            username=username,
            telegram_id=telegram_id,
            telegram_username=code_data['username'],
            telegram_first_name=code_data['first_name'],
            telegram_photo_url=code_data['photo_url'],
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update telegram info
        user.telegram_username = code_data['username']
        user.telegram_first_name = code_data['first_name']
        user.telegram_photo_url = code_data['photo_url']
        await db.commit()
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.get("/telegram/bot-username")
async def get_telegram_bot_username() -> dict:
    """Get Telegram bot username for auth link"""
    return {"bot_username": settings.TELEGRAM_BOT_USERNAME}


@router.post("/telegram/widget", response_model=schemas.Token)
async def telegram_widget_auth(
    *,
    db: AsyncSession = Depends(deps.get_db),
    auth_data: TelegramWidgetAuth,
) -> Any:
    """
    Authenticate via official Telegram Login Widget.
    Creates a new user if not exists.
    """
    # Verify hash
    if not verify_telegram_hash(auth_data):
        raise HTTPException(
            status_code=400,
            detail="Invalid Telegram authentication"
        )
    
    # Find or create user
    result = await db.execute(
        select(models.User).where(models.User.telegram_id == auth_data.id)
    )
    user = result.scalars().first()
    
    if not user:
        # Create new user
        username = auth_data.username or f"tg_{auth_data.id}"
        
        # Check if username exists
        result = await db.execute(
            select(models.User).where(models.User.username == username)
        )
        existing = result.scalars().first()
        if existing:
            import secrets as sec
            username = f"{username}_{sec.token_hex(3)}"
        
        user = models.User(
            username=username,
            telegram_id=auth_data.id,
            telegram_username=auth_data.username,
            telegram_first_name=auth_data.first_name,
            telegram_photo_url=auth_data.photo_url,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update telegram info
        user.telegram_username = auth_data.username
        user.telegram_first_name = auth_data.first_name
        user.telegram_photo_url = auth_data.photo_url
        await db.commit()
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
