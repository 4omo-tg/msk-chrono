from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.api.v1.endpoints.achievements import check_and_award_achievements

router = APIRouter()

@router.get("/", response_model=List[schemas.UserProgress])
async def read_user_progress(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve current user's progress.
    """
    result = await db.execute(
        select(models.UserProgress)
        .where(models.UserProgress.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/current", response_model=schemas.UserProgress)
async def get_current_progress(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current active (in_progress) route progress.
    """
    result = await db.execute(
        select(models.UserProgress)
        .where(models.UserProgress.user_id == current_user.id)
        .where(models.UserProgress.status == "in_progress")
        .limit(1)
    )
    progress = result.scalars().first()
    if not progress:
        raise HTTPException(status_code=404, detail="No active route")
    return progress

@router.post("/", response_model=schemas.UserProgress)
async def create_progress(
    *,
    db: AsyncSession = Depends(deps.get_db),
    progress_in: schemas.UserProgressCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create/Start progress for a route.
    """
    # Check if already exists
    result = await db.execute(
        select(models.UserProgress)
        .where(models.UserProgress.user_id == current_user.id)
        .where(models.UserProgress.route_id == progress_in.route_id)
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Progress for this route already exists")

    progress = models.UserProgress(
        user_id=current_user.id,
        route_id=progress_in.route_id,
        status=progress_in.status,
        completed_points_count=progress_in.completed_points_count
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress

@router.delete("/{progress_id}", response_model=schemas.UserProgress)
async def delete_progress(
    *,
    db: AsyncSession = Depends(deps.get_db),
    progress_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete/Reset progress for a route.
    """
    progress = await db.get(models.UserProgress, progress_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    if progress.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await db.delete(progress)
    await db.commit()
    return progress


@router.put("/{progress_id}", response_model=schemas.UserProgress)
async def update_progress(
    *,
    db: AsyncSession = Depends(deps.get_db),
    progress_id: int,
    progress_in: schemas.UserProgressUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update progress (e.g. status, count).
    """
    progress = await db.get(models.UserProgress, progress_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    if progress.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if progress_in.status is not None:
        progress.status = progress_in.status
    if progress_in.completed_points_count is not None:
        progress.completed_points_count = progress_in.completed_points_count
    
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress

@router.post("/check-in", response_model=schemas.CheckInResponse)
async def check_in(
    *,
    db: AsyncSession = Depends(deps.get_db),
    check_in_in: schemas.CheckIn,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Check-in at a POI, gain XP and update progress.
    """
    # 1. Get progress
    result = await db.execute(
        select(models.UserProgress)
        .where(models.UserProgress.user_id == current_user.id)
        .where(models.UserProgress.route_id == check_in_in.route_id)
    )
    progress = result.scalars().first()
    
    if not progress:
        raise HTTPException(
            status_code=400, 
            detail="You must start this route before checking in."
        )

    # 2. Get Route and Points to validate order
    # Need to load points to check order
    from sqlalchemy.orm import selectinload
    route_result = await db.execute(
        select(models.Route)
        .options(selectinload(models.Route.points))
        .where(models.Route.id == check_in_in.route_id)
    )
    route = route_result.scalars().first()
    if not route:
         raise HTTPException(status_code=404, detail="Route not found")

    # Check if already completed all
    if progress.completed_points_count >= len(route.points):
         raise HTTPException(status_code=400, detail="Route already completed!")

    # Get expected next POI
    # points are ordered by list index in the association match
    expected_poi = route.points[progress.completed_points_count]
    
    if expected_poi.id != check_in_in.poi_id:
        # Case 1: Use trying to check in to future point
        # Case 2: User trying to check in to ALREADY visited point (id matches previous)
        # We can be generic
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid check-in. You must visit '{expected_poi.title}' next."
        )

    # 3. Update progress
    progress.completed_points_count += 1
    
    # 4. Award XP
    xp_to_add = 50.0 # Fixed 50 XP per point/check-in
    bonus_xp = 0.0
    
    current_user.xp += xp_to_add
    
    # Check if route completion just happened
    if progress.completed_points_count >= len(route.points):
        progress.status = "completed"
        # Award Route Completion Bonus
        if route.reward_xp:
            bonus_xp = route.reward_xp
            current_user.xp += bonus_xp

    # Calculate new level
    # Formula derived from S = 25L^2 + 125L - 150
    # L = (-5 + sqrt(49 + 0.16 * XP)) / 2
    import math
    if current_user.xp > 0:
        new_level_float = (-5 + math.sqrt(49 + 0.16 * current_user.xp)) / 2
        new_level = math.floor(new_level_float)
    else:
        new_level = 1
        
    if new_level < 1: 
        new_level = 1
        
    current_user.level = new_level
    
    db.add(progress)
    db.add(current_user)
    
    await db.commit()
    await db.refresh(progress)
    await db.refresh(current_user)
    
    # Check for new achievements
    # Get updated stats
    result = await db.execute(
        select(models.UserProgress)
        .where(models.UserProgress.user_id == current_user.id)
    )
    all_progress = result.scalars().all()
    total_points = sum(p.completed_points_count for p in all_progress)
    completed_routes = sum(1 for p in all_progress if p.status == 'completed')
    
    # Get quiz count
    quiz_result = await db.execute(
        select(models.UserQuizProgress)
        .where(models.UserQuizProgress.user_id == current_user.id)
        .where(models.UserQuizProgress.is_correct == True)
    )
    total_quizzes = len(quiz_result.scalars().all())
    
    new_achievements = await check_and_award_achievements(
        db, current_user, total_points, completed_routes, total_quizzes
    )
    
    # Add achievement XP to response
    achievement_xp = sum(a.xp_reward for a in new_achievements)
    
    return {
        "updated_progress": progress,
        "xp_gained": xp_to_add + bonus_xp + achievement_xp,
        "new_total_xp": current_user.xp,
        "new_level": current_user.level,
        "new_achievements": [{
            "id": a.id,
            "code": a.code,
            "title": a.title,
            "description": a.description,
            "icon": a.icon,
            "xp_reward": a.xp_reward
        } for a in new_achievements]
    }
