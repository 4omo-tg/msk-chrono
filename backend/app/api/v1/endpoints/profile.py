"""Profile management endpoints"""
import json
import os
import uuid
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps

router = APIRouter()


@router.get("/me", response_model=schemas.UserProfile)
async def get_my_profile(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Получить свой профиль с полной информацией"""
    # Load user with relationships
    result = await db.execute(
        select(models.User)
        .options(
            selectinload(models.User.equipped_title),
            selectinload(models.User.equipped_frame),
            selectinload(models.User.unlocked_titles).selectinload(models.UserTitle.title),
            selectinload(models.User.unlocked_frames).selectinload(models.UserFrame.frame),
            selectinload(models.User.unlocked_badges).selectinload(models.UserBadge.badge),
            selectinload(models.User.achievements),
        )
        .where(models.User.id == current_user.id)
    )
    user = result.scalar_one()
    
    # Count friends
    friends_count = await db.scalar(
        select(func.count()).select_from(models.Friendship).where(models.Friendship.user_id == user.id)
    )
    
    # Parse equipped badges
    equipped_badges = []
    if user.equipped_badge_ids:
        try:
            badge_ids = json.loads(user.equipped_badge_ids)
            if badge_ids:
                badges_result = await db.execute(
                    select(models.Badge).where(models.Badge.id.in_(badge_ids))
                )
                equipped_badges = [schemas.BadgeOut.from_orm(b) for b in badges_result.scalars().all()]
        except:
            pass
    
    return schemas.UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        level=user.level,
        xp=user.xp,
        total_distance_km=user.total_distance_km or 0,
        total_time_minutes=user.total_time_minutes or 0,
        streak_days=user.streak_days or 0,
        reputation=user.reputation or 0,
        profile_background=user.profile_background,
        profile_visibility=user.profile_visibility,
        show_on_leaderboard=user.show_on_leaderboard,
        created_at=user.created_at,
        equipped_title_id=user.equipped_title_id,
        equipped_frame_id=user.equipped_frame_id,
        equipped_badge_ids=user.equipped_badge_ids,
        equipped_title=schemas.TitleOut.from_orm(user.equipped_title) if user.equipped_title else None,
        equipped_frame=schemas.FrameOut.from_orm(user.equipped_frame) if user.equipped_frame else None,
        equipped_badges=equipped_badges,
        unlocked_titles_count=len(user.unlocked_titles),
        unlocked_frames_count=len(user.unlocked_frames),
        unlocked_badges_count=len(user.unlocked_badges),
        friends_count=friends_count or 0,
        achievements_count=len(user.achievements),
        telegram_id=user.telegram_id,
        telegram_username=user.telegram_username,
        telegram_first_name=user.telegram_first_name,
        telegram_photo_url=user.telegram_photo_url,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
    )


@router.put("/me", response_model=schemas.User)
async def update_my_profile(
    *,
    db: AsyncSession = Depends(deps.get_db),
    profile_in: schemas.ProfileUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Обновить свой профиль"""
    if profile_in.display_name is not None:
        if len(profile_in.display_name) > 50:
            raise HTTPException(status_code=400, detail="Display name too long (max 50)")
        current_user.display_name = profile_in.display_name
    
    if profile_in.bio is not None:
        if len(profile_in.bio) > 500:
            raise HTTPException(status_code=400, detail="Bio too long (max 500)")
        current_user.bio = profile_in.bio
    
    if profile_in.equipped_title_id is not None:
        # Check if user has unlocked this title
        if profile_in.equipped_title_id > 0:
            unlocked = await db.scalar(
                select(models.UserTitle).where(
                    models.UserTitle.user_id == current_user.id,
                    models.UserTitle.title_id == profile_in.equipped_title_id
                )
            )
            if not unlocked:
                # Check if it's a default title
                title = await db.get(models.Title, profile_in.equipped_title_id)
                if not title or not title.is_default:
                    raise HTTPException(status_code=400, detail="Title not unlocked")
        current_user.equipped_title_id = profile_in.equipped_title_id if profile_in.equipped_title_id > 0 else None
    
    if profile_in.equipped_frame_id is not None:
        if profile_in.equipped_frame_id > 0:
            unlocked = await db.scalar(
                select(models.UserFrame).where(
                    models.UserFrame.user_id == current_user.id,
                    models.UserFrame.frame_id == profile_in.equipped_frame_id
                )
            )
            if not unlocked:
                frame = await db.get(models.ProfileFrame, profile_in.equipped_frame_id)
                if not frame or not frame.is_default:
                    raise HTTPException(status_code=400, detail="Frame not unlocked")
        current_user.equipped_frame_id = profile_in.equipped_frame_id if profile_in.equipped_frame_id > 0 else None
    
    if profile_in.equipped_badge_ids is not None:
        if len(profile_in.equipped_badge_ids) > 3:
            raise HTTPException(status_code=400, detail="Max 3 badges can be equipped")
        # Validate all badges are unlocked
        for badge_id in profile_in.equipped_badge_ids:
            unlocked = await db.scalar(
                select(models.UserBadge).where(
                    models.UserBadge.user_id == current_user.id,
                    models.UserBadge.badge_id == badge_id
                )
            )
            if not unlocked:
                badge = await db.get(models.Badge, badge_id)
                if not badge or not badge.is_default:
                    raise HTTPException(status_code=400, detail=f"Badge {badge_id} not unlocked")
        current_user.equipped_badge_ids = json.dumps(profile_in.equipped_badge_ids)
    
    if profile_in.profile_background is not None:
        current_user.profile_background = profile_in.profile_background
    
    if profile_in.profile_visibility is not None:
        if profile_in.profile_visibility not in ["public", "friends", "private"]:
            raise HTTPException(status_code=400, detail="Invalid visibility")
        current_user.profile_visibility = profile_in.profile_visibility
    
    if profile_in.show_on_leaderboard is not None:
        current_user.show_on_leaderboard = profile_in.show_on_leaderboard
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Загрузить аватар"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    
    # Save file
    uploads_dir = os.environ.get("UPLOADS_DIR", "uploads")
    upload_dir = os.path.join(uploads_dir, "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Update user
    current_user.avatar_url = f"/uploads/avatars/{filename}"
    db.add(current_user)
    await db.commit()
    
    return {"avatar_url": current_user.avatar_url}


@router.get("/{user_id}", response_model=schemas.PublicProfile)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_user_optional),
) -> Any:
    """Получить публичный профиль пользователя"""
    result = await db.execute(
        select(models.User)
        .options(
            selectinload(models.User.equipped_title),
            selectinload(models.User.equipped_frame),
            selectinload(models.User.achievements),
        )
        .where(models.User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check visibility
    is_self = current_user and current_user.id == user_id
    is_friend = False
    friend_request_sent = False
    friend_request_received = False
    
    if current_user and not is_self:
        # Check friendship
        friendship = await db.scalar(
            select(models.Friendship).where(
                models.Friendship.user_id == current_user.id,
                models.Friendship.friend_id == user_id
            )
        )
        is_friend = friendship is not None
        
        # Check friend requests
        sent = await db.scalar(
            select(models.FriendRequest).where(
                models.FriendRequest.from_user_id == current_user.id,
                models.FriendRequest.to_user_id == user_id,
                models.FriendRequest.status == "pending"
            )
        )
        friend_request_sent = sent is not None
        
        received = await db.scalar(
            select(models.FriendRequest).where(
                models.FriendRequest.from_user_id == user_id,
                models.FriendRequest.to_user_id == current_user.id,
                models.FriendRequest.status == "pending"
            )
        )
        friend_request_received = received is not None
    
    # Check if profile is visible
    if not is_self:
        if user.profile_visibility == "private":
            raise HTTPException(status_code=403, detail="Profile is private")
        if user.profile_visibility == "friends" and not is_friend:
            raise HTTPException(status_code=403, detail="Profile is friends-only")
    
    # Count friends
    friends_count = await db.scalar(
        select(func.count()).select_from(models.Friendship).where(models.Friendship.user_id == user_id)
    )
    
    # Parse equipped badges
    equipped_badges = []
    if user.equipped_badge_ids:
        try:
            badge_ids = json.loads(user.equipped_badge_ids)
            if badge_ids:
                badges_result = await db.execute(
                    select(models.Badge).where(models.Badge.id.in_(badge_ids))
                )
                equipped_badges = [schemas.BadgeOut.from_orm(b) for b in badges_result.scalars().all()]
        except:
            pass
    
    return schemas.PublicProfile(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        level=user.level,
        xp=user.xp,
        reputation=user.reputation or 0,
        profile_background=user.profile_background,
        equipped_title=schemas.TitleOut.from_orm(user.equipped_title) if user.equipped_title else None,
        equipped_frame=schemas.FrameOut.from_orm(user.equipped_frame) if user.equipped_frame else None,
        equipped_badges=equipped_badges,
        achievements_count=len(user.achievements),
        friends_count=friends_count or 0,
        total_distance_km=user.total_distance_km or 0,
        streak_days=user.streak_days or 0,
        created_at=user.created_at,
        is_friend=is_friend,
        friend_request_sent=friend_request_sent,
        friend_request_received=friend_request_received,
    )


@router.get("/search", response_model=list[schemas.UserSearchResult])
async def search_users(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    limit: int = 20,
) -> Any:
    """Поиск пользователей"""
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.equipped_title), selectinload(models.User.equipped_frame))
        .where(
            or_(
                models.User.username.ilike(f"%{q}%"),
                models.User.display_name.ilike(f"%{q}%")
            ),
            models.User.id != current_user.id,
            models.User.profile_visibility != "private"
        )
        .limit(limit)
    )
    users = result.scalars().all()
    
    # Get friend IDs
    friends_result = await db.execute(
        select(models.Friendship.friend_id).where(models.Friendship.user_id == current_user.id)
    )
    friend_ids = set(friends_result.scalars().all())
    
    return [
        schemas.UserSearchResult(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            avatar_url=u.avatar_url,
            level=u.level,
            equipped_title=schemas.TitleOut.from_orm(u.equipped_title) if u.equipped_title else None,
            equipped_frame=schemas.FrameOut.from_orm(u.equipped_frame) if u.equipped_frame else None,
            is_friend=u.id in friend_ids,
        )
        for u in users
    ]
