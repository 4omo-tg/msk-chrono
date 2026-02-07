"""Cosmetics system endpoints - Titles, Frames, Badges"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps

router = APIRouter()


# ============== TITLES ==============

@router.get("/titles", response_model=list[schemas.CosmeticTitleOut])
async def get_all_titles(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Получить все титулы с инфой о разблокировке"""
    # Get all titles
    titles_result = await db.execute(select(models.Title))
    titles = titles_result.scalars().all()
    
    # Get user's unlocked titles
    unlocked_result = await db.execute(
        select(models.UserTitle).where(models.UserTitle.user_id == current_user.id)
    )
    unlocked = {ut.title_id: ut.unlocked_at for ut in unlocked_result.scalars().all()}
    
    return [
        schemas.CosmeticTitleOut(
            id=t.id,
            code=t.code,
            name=t.name,
            description=t.description,
            color=t.color,
            rarity=t.rarity,
            unlock_type=t.unlock_type,
            unlock_value=t.unlock_value,
            is_default=t.is_default,
            unlocked=t.is_default or t.id in unlocked,
            unlocked_at=unlocked.get(t.id),
        )
        for t in titles
    ]


@router.post("/titles/{title_id}/equip")
async def equip_title(
    title_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Надеть титул"""
    if title_id == 0:
        current_user.equipped_title_id = None
        await db.commit()
        return {"message": "Title unequipped"}
    
    title = await db.get(models.Title, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    
    # Check if unlocked or default
    if not title.is_default:
        unlocked = await db.scalar(
            select(models.UserTitle).where(
                models.UserTitle.user_id == current_user.id,
                models.UserTitle.title_id == title_id
            )
        )
        if not unlocked:
            raise HTTPException(status_code=403, detail="Title not unlocked")
    
    current_user.equipped_title_id = title_id
    await db.commit()
    
    return {"message": "Title equipped"}


# ============== FRAMES ==============

@router.get("/frames", response_model=list[schemas.CosmeticFrameOut])
async def get_all_frames(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Получить все рамки"""
    frames_result = await db.execute(select(models.ProfileFrame))
    frames = frames_result.scalars().all()
    
    unlocked_result = await db.execute(
        select(models.UserFrame).where(models.UserFrame.user_id == current_user.id)
    )
    unlocked = {uf.frame_id: uf.unlocked_at for uf in unlocked_result.scalars().all()}
    
    return [
        schemas.CosmeticFrameOut(
            id=f.id,
            code=f.code,
            name=f.name,
            description=f.description,
            image_url=f.image_url,
            css_class=f.css_class,
            rarity=f.rarity,
            unlock_type=f.unlock_type,
            unlock_value=f.unlock_value,
            is_default=f.is_default,
            unlocked=f.is_default or f.id in unlocked,
            unlocked_at=unlocked.get(f.id),
        )
        for f in frames
    ]


@router.post("/frames/{frame_id}/equip")
async def equip_frame(
    frame_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Надеть рамку"""
    if frame_id == 0:
        current_user.equipped_frame_id = None
        await db.commit()
        return {"message": "Frame unequipped"}
    
    frame = await db.get(models.ProfileFrame, frame_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    
    if not frame.is_default:
        unlocked = await db.scalar(
            select(models.UserFrame).where(
                models.UserFrame.user_id == current_user.id,
                models.UserFrame.frame_id == frame_id
            )
        )
        if not unlocked:
            raise HTTPException(status_code=403, detail="Frame not unlocked")
    
    current_user.equipped_frame_id = frame_id
    await db.commit()
    
    return {"message": "Frame equipped"}


# ============== BADGES ==============

@router.get("/badges", response_model=list[schemas.CosmeticBadgeOut])
async def get_all_badges(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Получить все бейджи"""
    badges_result = await db.execute(select(models.Badge))
    badges = badges_result.scalars().all()
    
    unlocked_result = await db.execute(
        select(models.UserBadge).where(models.UserBadge.user_id == current_user.id)
    )
    unlocked = {ub.badge_id: ub.unlocked_at for ub in unlocked_result.scalars().all()}
    
    return [
        schemas.CosmeticBadgeOut(
            id=b.id,
            code=b.code,
            name=b.name,
            description=b.description,
            icon=b.icon,
            color=b.color,
            rarity=b.rarity,
            unlock_type=b.unlock_type,
            unlock_value=b.unlock_value,
            is_default=b.is_default,
            unlocked=b.is_default or b.id in unlocked,
            unlocked_at=unlocked.get(b.id),
        )
        for b in badges
    ]


@router.post("/badges/equip")
async def equip_badges(
    data: schemas.EquipBadges,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Надеть бейджи (макс 3)"""
    import json
    
    if len(data.badge_ids) > 3:
        raise HTTPException(status_code=400, detail="Max 3 badges")
    
    # Validate all badges are unlocked
    for badge_id in data.badge_ids:
        badge = await db.get(models.Badge, badge_id)
        if not badge:
            raise HTTPException(status_code=404, detail=f"Badge {badge_id} not found")
        
        if not badge.is_default:
            unlocked = await db.scalar(
                select(models.UserBadge).where(
                    models.UserBadge.user_id == current_user.id,
                    models.UserBadge.badge_id == badge_id
                )
            )
            if not unlocked:
                raise HTTPException(status_code=403, detail=f"Badge {badge_id} not unlocked")
    
    current_user.equipped_badge_ids = json.dumps(data.badge_ids) if data.badge_ids else None
    await db.commit()
    
    return {"message": "Badges equipped"}


# ============== UNLOCK CHECKING ==============

async def check_and_unlock_cosmetics(
    db: AsyncSession,
    user: models.User,
) -> list[dict]:
    """Проверяет и разблокирует новые косметические предметы"""
    newly_unlocked = []
    
    # Get user's achievements
    achievements_result = await db.execute(
        select(models.UserAchievement)
        .options(selectinload(models.UserAchievement.achievement))
        .where(models.UserAchievement.user_id == user.id)
    )
    user_achievements = {ua.achievement.code for ua in achievements_result.scalars().all()}
    
    # Check titles
    titles_result = await db.execute(select(models.Title).where(models.Title.is_default == False))
    for title in titles_result.scalars().all():
        # Check if already unlocked
        existing = await db.scalar(
            select(models.UserTitle).where(
                models.UserTitle.user_id == user.id,
                models.UserTitle.title_id == title.id
            )
        )
        if existing:
            continue
        
        # Check unlock condition
        unlocked = False
        if title.unlock_type == "level" and title.unlock_value:
            if user.level >= int(title.unlock_value):
                unlocked = True
        elif title.unlock_type == "achievement" and title.unlock_value:
            if title.unlock_value in user_achievements:
                unlocked = True
        
        if unlocked:
            user_title = models.UserTitle(user_id=user.id, title_id=title.id)
            db.add(user_title)
            newly_unlocked.append({"type": "title", "name": title.name, "rarity": title.rarity})
    
    # Check frames
    frames_result = await db.execute(select(models.ProfileFrame).where(models.ProfileFrame.is_default == False))
    for frame in frames_result.scalars().all():
        existing = await db.scalar(
            select(models.UserFrame).where(
                models.UserFrame.user_id == user.id,
                models.UserFrame.frame_id == frame.id
            )
        )
        if existing:
            continue
        
        unlocked = False
        if frame.unlock_type == "level" and frame.unlock_value:
            if user.level >= int(frame.unlock_value):
                unlocked = True
        elif frame.unlock_type == "achievement" and frame.unlock_value:
            if frame.unlock_value in user_achievements:
                unlocked = True
        
        if unlocked:
            user_frame = models.UserFrame(user_id=user.id, frame_id=frame.id)
            db.add(user_frame)
            newly_unlocked.append({"type": "frame", "name": frame.name, "rarity": frame.rarity})
    
    # Check badges
    badges_result = await db.execute(select(models.Badge).where(models.Badge.is_default == False))
    for badge in badges_result.scalars().all():
        existing = await db.scalar(
            select(models.UserBadge).where(
                models.UserBadge.user_id == user.id,
                models.UserBadge.badge_id == badge.id
            )
        )
        if existing:
            continue
        
        unlocked = False
        if badge.unlock_type == "level" and badge.unlock_value:
            if user.level >= int(badge.unlock_value):
                unlocked = True
        elif badge.unlock_type == "achievement" and badge.unlock_value:
            if badge.unlock_value in user_achievements:
                unlocked = True
        
        if unlocked:
            user_badge = models.UserBadge(user_id=user.id, badge_id=badge.id)
            db.add(user_badge)
            newly_unlocked.append({"type": "badge", "name": badge.name, "rarity": badge.rarity})
    
    if newly_unlocked:
        await db.commit()
    
    return newly_unlocked
