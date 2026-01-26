from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas
from app.api import deps
from app.api.v1.endpoints.achievements import check_and_award_achievements
import math

router = APIRouter()

@router.get("/", response_model=List[schemas.Quiz])
async def list_quizzes(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """List all quizzes (admin only)"""
    result = await db.execute(select(models.Quiz).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/poi/{poi_id}", response_model=List[schemas.QuizPublic])
async def get_quizzes_for_poi(
    poi_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all quizzes for a specific POI (public version without correct answer)"""
    result = await db.execute(
        select(models.Quiz).where(models.Quiz.poi_id == poi_id)
    )
    quizzes = result.scalars().all()
    
    # Check which quizzes user has already completed
    quiz_ids = [q.id for q in quizzes]
    if quiz_ids:
        progress_result = await db.execute(
            select(models.UserQuizProgress).where(
                models.UserQuizProgress.user_id == current_user.id,
                models.UserQuizProgress.quiz_id.in_(quiz_ids)
            )
        )
        completed_quiz_ids = {p.quiz_id for p in progress_result.scalars().all()}
        
        # Filter out completed quizzes
        quizzes = [q for q in quizzes if q.id not in completed_quiz_ids]
    
    return quizzes

@router.get("/{quiz_id}", response_model=schemas.Quiz)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get quiz by ID (admin only)"""
    quiz = await db.get(models.Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

@router.post("/", response_model=schemas.Quiz)
async def create_quiz(
    *,
    db: AsyncSession = Depends(deps.get_db),
    quiz_in: schemas.QuizCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Create new quiz (admin only)"""
    quiz = models.Quiz(**quiz_in.model_dump())
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz

@router.put("/{quiz_id}", response_model=schemas.Quiz)
async def update_quiz(
    *,
    db: AsyncSession = Depends(deps.get_db),
    quiz_id: int,
    quiz_in: schemas.QuizUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Update quiz (admin only)"""
    quiz = await db.get(models.Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    update_data = quiz_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quiz, field, value)
    
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz

@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Delete quiz (admin only)"""
    quiz = await db.get(models.Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    await db.delete(quiz)
    await db.commit()
    return {"ok": True}

@router.post("/{quiz_id}/submit", response_model=schemas.QuizSubmitResponse)
async def submit_quiz_answer(
    *,
    db: AsyncSession = Depends(deps.get_db),
    quiz_id: int,
    answer_in: schemas.QuizSubmit,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Submit quiz answer and get XP if correct"""
    # Get quiz
    quiz = await db.get(models.Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check if user already completed this quiz
    result = await db.execute(
        select(models.UserQuizProgress).where(
            models.UserQuizProgress.user_id == current_user.id,
            models.UserQuizProgress.quiz_id == quiz_id
        )
    )
    existing_progress = result.scalars().first()
    if existing_progress:
        raise HTTPException(status_code=400, detail="Quiz already completed")
    
    # Check answer
    is_correct = answer_in.answer.upper() == quiz.correct_answer.upper()
    xp_earned = quiz.xp_reward if is_correct else 0.0
    
    # Update user XP
    if is_correct:
        current_user.xp += xp_earned
    
    # Calculate new level
    if current_user.xp > 0:
        new_level_float = (-5 + math.sqrt(49 + 0.16 * current_user.xp)) / 2
        new_level = math.floor(new_level_float)
    else:
        new_level = 1
    
    if new_level < 1:
        new_level = 1
    
    current_user.level = new_level
    
    # Save progress
    progress = models.UserQuizProgress(
        user_id=current_user.id,
        quiz_id=quiz_id,
        is_correct=is_correct
    )
    db.add(progress)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    # Check for quiz achievements if correct
    new_achievements = []
    if is_correct:
        # Get stats for achievements
        progress_result = await db.execute(
            select(models.UserProgress)
            .where(models.UserProgress.user_id == current_user.id)
        )
        all_progress = progress_result.scalars().all()
        total_points = sum(p.completed_points_count for p in all_progress)
        completed_routes = sum(1 for p in all_progress if p.status == 'completed')
        
        quiz_result = await db.execute(
            select(models.UserQuizProgress)
            .where(models.UserQuizProgress.user_id == current_user.id)
            .where(models.UserQuizProgress.is_correct == True)
        )
        total_quizzes = len(quiz_result.scalars().all())
        
        new_achievements = await check_and_award_achievements(
            db, current_user, total_points, completed_routes, total_quizzes
        )
        await db.refresh(current_user)
    
    return {
        "is_correct": is_correct,
        "xp_earned": xp_earned,
        "correct_answer": quiz.correct_answer,
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
