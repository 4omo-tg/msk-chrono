from typing import Any, List
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps
from app.models.learning import (
    LearningModule, LearningLesson, LearningQuestion,
    UserLearningProgress, UserLessonProgress, UserQuestionHistory, LearningSession,
)
from app.schemas.learning import (
    ModuleWithProgressOut, LessonWithProgressOut, LessonDetailOut,
    LearningQuestionOut, StartSessionRequest, SessionOut,
    AnswerRequest, AnswerResultOut, SessionCompleteOut,
    UserLearningProgressOut, SetDailyGoalRequest,
    LearningDashboardOut, LeagueLeaderboardOut, LeagueUserOut,
)

router = APIRouter()


# ── helpers ────────────────────────────────────────────────────────────────────

async def _get_or_create_progress(
    db: AsyncSession, user_id: int
) -> UserLearningProgress:
    """Return the user's learning progress row, creating one if absent."""
    result = await db.execute(
        select(UserLearningProgress).where(UserLearningProgress.user_id == user_id)
    )
    progress = result.scalars().first()
    if not progress:
        progress = UserLearningProgress(user_id=user_id)
        db.add(progress)
        await db.flush()
    return progress


def _update_streak(progress: UserLearningProgress) -> None:
    """Bump current_streak / longest_streak based on last_activity_date."""
    now = datetime.now(timezone.utc)
    today = now.date()

    if progress.last_activity_date is None:
        progress.current_streak = 1
    else:
        last = progress.last_activity_date
        if hasattr(last, "date"):
            last = last.date()
        delta = (today - last).days
        if delta == 0:
            # already counted today – nothing to do
            pass
        elif delta == 1:
            progress.current_streak += 1
        else:
            progress.current_streak = 1

    if progress.current_streak > progress.longest_streak:
        progress.longest_streak = progress.current_streak

    progress.last_activity_date = now


# ── GET /modules ───────────────────────────────────────────────────────────────

@router.get("/modules", response_model=List[ModuleWithProgressOut])
async def list_modules(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """List active learning modules with user progress."""
    result = await db.execute(
        select(LearningModule)
        .where(LearningModule.is_active == True)  # noqa: E712
        .options(selectinload(LearningModule.lessons))
        .order_by(LearningModule.order)
    )
    modules = result.scalars().all()

    # Fetch all completed lesson ids for this user in one query
    ulp_result = await db.execute(
        select(UserLessonProgress.lesson_id).where(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.is_completed == True,  # noqa: E712
        )
    )
    completed_lesson_ids = set(ulp_result.scalars().all())

    out: list[ModuleWithProgressOut] = []
    for m in modules:
        total = len(m.lessons)
        completed = sum(1 for l in m.lessons if l.id in completed_lesson_ids)
        pct = round(completed / total * 100, 1) if total else 0.0
        out.append(
            ModuleWithProgressOut(
                **{
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "icon": m.icon,
                    "order": m.order,
                    "is_active": m.is_active,
                    "created_at": m.created_at,
                    "total_lessons": total,
                    "completed_lessons": completed,
                    "progress_pct": pct,
                }
            )
        )
    return out


# ── GET /modules/{module_id}/lessons ───────────────────────────────────────────

@router.get("/modules/{module_id}/lessons", response_model=List[LessonWithProgressOut])
async def list_lessons(
    module_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """List lessons for a module, enriched with user progress."""
    module = await db.get(LearningModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    result = await db.execute(
        select(LearningLesson)
        .where(LearningLesson.module_id == module_id)
        .order_by(LearningLesson.order)
    )
    lessons = result.scalars().all()

    lesson_ids = [l.id for l in lessons]
    ulp_result = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.lesson_id.in_(lesson_ids),
        )
    )
    progress_map = {p.lesson_id: p for p in ulp_result.scalars().all()}

    out: list[LessonWithProgressOut] = []
    for l in lessons:
        p = progress_map.get(l.id)
        out.append(
            LessonWithProgressOut(
                id=l.id,
                module_id=l.module_id,
                title=l.title,
                description=l.description,
                order=l.order,
                xp_reward=l.xp_reward,
                created_at=l.created_at,
                is_completed=p.is_completed if p else False,
                best_score=p.best_score if p else 0,
                attempts=p.attempts if p else 0,
            )
        )
    return out


# ── GET /lessons/{lesson_id} ──────────────────────────────────────────────────

@router.get("/lessons/{lesson_id}", response_model=LessonDetailOut)
async def get_lesson_detail(
    lesson_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get full lesson detail with questions (correct answers hidden)."""
    result = await db.execute(
        select(LearningLesson)
        .where(LearningLesson.id == lesson_id)
        .options(selectinload(LearningLesson.questions))
    )
    lesson = result.scalars().first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # User progress for this lesson
    ulp_result = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.lesson_id == lesson_id,
        )
    )
    ulp = ulp_result.scalars().first()

    questions = [
        LearningQuestionOut(
            id=q.id,
            lesson_id=q.lesson_id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            order=q.order,
        )
        for q in sorted(lesson.questions, key=lambda q: q.order)
    ]

    return LessonDetailOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        description=lesson.description,
        order=lesson.order,
        xp_reward=lesson.xp_reward,
        created_at=lesson.created_at,
        questions=questions,
        total_questions=len(questions),
        is_completed=ulp.is_completed if ulp else False,
        best_score=ulp.best_score if ulp else 0,
    )


# ── POST /sessions/start ──────────────────────────────────────────────────────

@router.post("/sessions/start", response_model=SessionOut)
async def start_session(
    body: StartSessionRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Start a new learning session for a lesson."""
    lesson = await db.get(LearningLesson, body.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    session = LearningSession(
        user_id=current_user.id,
        lesson_id=body.lesson_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


# ── POST /sessions/{session_id}/answer ────────────────────────────────────────

@router.post("/sessions/{session_id}/answer", response_model=AnswerResultOut)
async def answer_question(
    session_id: int,
    body: AnswerRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Submit an answer for a question within an active session."""
    session = await db.get(LearningSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.completed_at is not None:
        raise HTTPException(status_code=400, detail="Session already completed")

    question = await db.get(LearningQuestion, body.question_id)
    if not question or question.lesson_id != session.lesson_id:
        raise HTTPException(status_code=404, detail="Question not found in this session's lesson")

    is_correct = body.answer.strip().lower() == question.correct_answer.strip().lower()

    # Record history
    history = UserQuestionHistory(
        user_id=current_user.id,
        question_id=question.id,
        is_correct=is_correct,
    )
    db.add(history)

    xp = 0
    if is_correct:
        lesson = await db.get(LearningLesson, session.lesson_id)
        # Distribute lesson XP equally among questions
        q_count_result = await db.execute(
            select(func.count(LearningQuestion.id)).where(
                LearningQuestion.lesson_id == session.lesson_id
            )
        )
        q_count = q_count_result.scalar() or 1
        xp = max(1, (lesson.xp_reward if lesson else 10) // q_count)
        session.xp_earned += xp

    await db.commit()

    return AnswerResultOut(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        xp_earned=xp,
    )


# ── POST /sessions/{session_id}/complete ──────────────────────────────────────

@router.post("/sessions/{session_id}/complete", response_model=SessionCompleteOut)
async def complete_session(
    session_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Mark a learning session as complete and update all progress."""
    session = await db.get(LearningSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.completed_at is not None:
        raise HTTPException(status_code=400, detail="Session already completed")

    session.completed_at = datetime.now(timezone.utc)

    # Calculate score from question history for this session's lesson
    hist_result = await db.execute(
        select(UserQuestionHistory).where(
            UserQuestionHistory.user_id == current_user.id,
            UserQuestionHistory.question_id.in_(
                select(LearningQuestion.id).where(
                    LearningQuestion.lesson_id == session.lesson_id
                )
            ),
            UserQuestionHistory.answered_at >= session.started_at,
        )
    )
    history_rows = hist_result.scalars().all()
    total_q = len(history_rows) or 1
    correct_q = sum(1 for h in history_rows if h.is_correct)
    score = round(correct_q / total_q * 100)
    session.score = score

    # Update lesson progress
    ulp_result = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.lesson_id == session.lesson_id,
        )
    )
    ulp = ulp_result.scalars().first()
    is_new_best = False
    if not ulp:
        ulp = UserLessonProgress(
            user_id=current_user.id,
            lesson_id=session.lesson_id,
        )
        db.add(ulp)

    ulp.attempts += 1
    ulp.last_attempt_at = session.completed_at
    if score > ulp.best_score:
        ulp.best_score = score
        is_new_best = True
    if score >= 70:  # 70 % threshold to "complete"
        ulp.is_completed = True

    # Update user learning progress (XP, streak)
    progress = await _get_or_create_progress(db, current_user.id)
    progress.total_xp += session.xp_earned
    _update_streak(progress)

    # Promote league based on XP thresholds
    xp = progress.total_xp
    if xp >= 5000:
        progress.league = "diamond"
    elif xp >= 2500:
        progress.league = "platinum"
    elif xp >= 1000:
        progress.league = "gold"
    elif xp >= 300:
        progress.league = "silver"
    else:
        progress.league = "bronze"

    await db.commit()

    return SessionCompleteOut(
        session_id=session.id,
        score=score,
        xp_earned=session.xp_earned,
        total_correct=correct_q,
        total_questions=len(history_rows),
        is_new_best=is_new_best,
        streak=progress.current_streak,
    )


# ── GET /dashboard ─────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=LearningDashboardOut)
async def get_dashboard(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Return the user's learning dashboard."""
    progress = await _get_or_create_progress(db, current_user.id)

    # Today's XP: sum of xp_earned from sessions completed today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.coalesce(func.sum(LearningSession.xp_earned), 0)).where(
            LearningSession.user_id == current_user.id,
            LearningSession.completed_at >= today_start,
        )
    )
    today_xp: int = today_result.scalar() or 0

    # Modules with progress (reuse list_modules logic inline)
    mod_result = await db.execute(
        select(LearningModule)
        .where(LearningModule.is_active == True)  # noqa: E712
        .options(selectinload(LearningModule.lessons))
        .order_by(LearningModule.order)
    )
    modules = mod_result.scalars().all()

    ulp_result = await db.execute(
        select(UserLessonProgress.lesson_id).where(
            UserLessonProgress.user_id == current_user.id,
            UserLessonProgress.is_completed == True,  # noqa: E712
        )
    )
    completed_ids = set(ulp_result.scalars().all())

    modules_out = []
    for m in modules:
        total = len(m.lessons)
        completed = sum(1 for l in m.lessons if l.id in completed_ids)
        modules_out.append(
            ModuleWithProgressOut(
                id=m.id,
                title=m.title,
                description=m.description,
                icon=m.icon,
                order=m.order,
                is_active=m.is_active,
                created_at=m.created_at,
                total_lessons=total,
                completed_lessons=completed,
                progress_pct=round(completed / total * 100, 1) if total else 0.0,
            )
        )

    await db.commit()  # flush any newly-created progress row

    return LearningDashboardOut(
        progress=UserLearningProgressOut.model_validate(progress),
        modules=modules_out,
        today_xp=today_xp,
        daily_goal_met=today_xp >= progress.daily_goal,
    )


# ── PUT /daily-goal ────────────────────────────────────────────────────────────

@router.put("/daily-goal", response_model=UserLearningProgressOut)
async def set_daily_goal(
    body: SetDailyGoalRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Set the user's daily XP goal."""
    if body.daily_goal < 1:
        raise HTTPException(status_code=400, detail="Daily goal must be at least 1")

    progress = await _get_or_create_progress(db, current_user.id)
    progress.daily_goal = body.daily_goal
    await db.commit()
    await db.refresh(progress)
    return progress
