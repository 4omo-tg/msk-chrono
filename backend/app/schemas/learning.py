from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


# ── Module schemas ──────────────────────────────────────────────────────────

class LearningModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    icon: str = "BookOpen"
    order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None


class ModuleWithProgressOut(LearningModuleOut):
    """Module enriched with per-user progress info."""
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_pct: float = 0.0  # 0-100


# ── Lesson schemas ──────────────────────────────────────────────────────────

class LearningLessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    title: str
    description: Optional[str] = None
    order: int = 0
    xp_reward: int = 10
    created_at: Optional[datetime] = None


class LessonWithProgressOut(LearningLessonOut):
    """Lesson enriched with per-user progress info."""
    is_completed: bool = False
    best_score: int = 0
    attempts: int = 0


# ── Question schemas ────────────────────────────────────────────────────────

class LearningQuestionOut(BaseModel):
    """Public-facing question (no correct answer exposed)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    question_text: str
    question_type: str = "multiple_choice"
    options: Optional[List[str]] = None
    order: int = 0


class QuestionWithAnswerOut(LearningQuestionOut):
    """Admin / post-answer view that includes the correct answer & explanation."""
    correct_answer: str
    explanation: Optional[str] = None


class LessonDetailOut(LearningLessonOut):
    """Lesson with its questions (for the lesson screen)."""
    questions: List[LearningQuestionOut] = []
    total_questions: int = 0
    is_completed: bool = False
    best_score: int = 0


# ── Session schemas ─────────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    lesson_id: int


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    lesson_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: int = 0
    xp_earned: int = 0


class AnswerRequest(BaseModel):
    question_id: int
    answer: str


class AnswerResultOut(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    xp_earned: int = 0


class SessionCompleteOut(BaseModel):
    session_id: int
    score: int  # percentage 0-100
    xp_earned: int
    total_correct: int
    total_questions: int
    is_new_best: bool = False
    streak: int = 0


# ── User learning progress schemas ─────────────────────────────────────────

class UserLearningProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    total_xp: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    daily_goal: int = 10
    last_activity_date: Optional[datetime] = None
    league: str = "bronze"


class SetDailyGoalRequest(BaseModel):
    daily_goal: int  # XP per day


# ── Dashboard / leaderboard schemas ────────────────────────────────────────

class LearningDashboardOut(BaseModel):
    progress: UserLearningProgressOut
    modules: List[ModuleWithProgressOut] = []
    today_xp: int = 0
    daily_goal_met: bool = False


class LeagueUserOut(BaseModel):
    user_id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_xp: int = 0


class LeagueLeaderboardOut(BaseModel):
    league: str
    users: List[LeagueUserOut] = []
