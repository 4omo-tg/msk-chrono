from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps

router = APIRouter()


async def check_and_award_achievements(
    db: AsyncSession,
    user: models.User,
    total_points: int,
    completed_routes: int,
    total_quizzes: int = 0
) -> List[models.Achievement]:
    """
    Check if user qualifies for any new achievements and award them.
    Returns list of newly unlocked achievements.
    """
    # Get all achievements
    result = await db.execute(select(models.Achievement))
    all_achievements = result.scalars().all()
    
    # Get user's current achievements
    result = await db.execute(
        select(models.UserAchievement.achievement_id)
        .where(models.UserAchievement.user_id == user.id)
    )
    unlocked_ids = set(row[0] for row in result.all())
    
    new_achievements = []
    total_bonus_xp = 0.0
    
    for achievement in all_achievements:
        # Skip if already unlocked
        if achievement.id in unlocked_ids:
            continue
            
        # Check condition
        unlocked = False
        if achievement.condition_type == 'points':
            unlocked = total_points >= achievement.condition_value
        elif achievement.condition_type == 'routes':
            unlocked = completed_routes >= achievement.condition_value
        elif achievement.condition_type == 'level':
            unlocked = user.level >= achievement.condition_value
        elif achievement.condition_type == 'quizzes':
            unlocked = total_quizzes >= achievement.condition_value
        
        if unlocked:
            # Award achievement
            user_achievement = models.UserAchievement(
                user_id=user.id,
                achievement_id=achievement.id
            )
            db.add(user_achievement)
            new_achievements.append(achievement)
            
            # Award bonus XP
            if achievement.xp_reward > 0:
                user.xp += achievement.xp_reward
                total_bonus_xp += achievement.xp_reward
    
    if new_achievements:
        # Recalculate level if XP changed
        if total_bonus_xp > 0:
            import math
            if user.xp > 0:
                new_level = int((-5 + math.sqrt(49 + 0.16 * user.xp)) / 2)
                user.level = max(1, new_level)
        
        db.add(user)
        await db.commit()
    
    return new_achievements


@router.get("", response_model=List[schemas.AchievementWithStatus])
async def get_achievements(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all achievements with unlock status for current user.
    """
    # Get all achievements
    result = await db.execute(select(models.Achievement))
    all_achievements = result.scalars().all()
    
    # Get user's unlocked achievements
    result = await db.execute(
        select(models.UserAchievement)
        .where(models.UserAchievement.user_id == current_user.id)
    )
    user_achievements = {ua.achievement_id: ua for ua in result.scalars().all()}
    
    # Build response
    response = []
    for ach in all_achievements:
        ua = user_achievements.get(ach.id)
        response.append(schemas.AchievementWithStatus(
            id=ach.id,
            code=ach.code,
            title=ach.title,
            description=ach.description,
            icon=ach.icon,
            xp_reward=ach.xp_reward,
            condition_type=ach.condition_type,
            condition_value=ach.condition_value,
            unlocked=ua is not None,
            unlocked_at=ua.unlocked_at if ua else None
        ))
    
    return response


@router.post("/check", response_model=schemas.NewAchievementsResponse)
async def check_achievements(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Check and award any new achievements for current user.
    Call this after completing actions that might trigger achievements.
    """
    # Get user stats
    result = await db.execute(
        select(models.UserProgress)
        .where(models.UserProgress.user_id == current_user.id)
    )
    progress_list = result.scalars().all()
    
    total_points = sum(p.completed_points_count for p in progress_list)
    completed_routes = sum(1 for p in progress_list if p.status == 'completed')
    
    # Check and award
    new_achievements = await check_and_award_achievements(
        db, current_user, total_points, completed_routes
    )
    
    total_xp = sum(a.xp_reward for a in new_achievements)
    
    return schemas.NewAchievementsResponse(
        new_achievements=[schemas.Achievement.model_validate(a) for a in new_achievements],
        xp_gained=total_xp
    )
