from datetime import timedelta
from typing import Any

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
    from app.telegram_bot import get_and_consume_code
    
    # Get and validate code
    code_data = get_and_consume_code(auth_data.code)
    if not code_data:
        raise HTTPException(
            status_code=400,
            detail="Неверный или истекший код"
        )
    
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
