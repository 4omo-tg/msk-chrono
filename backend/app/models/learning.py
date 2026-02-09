from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, JSON, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class LearningModule(Base):
    """A learning module (e.g., 'Medieval Moscow', 'Soviet Architecture')"""
    __tablename__ = "learning_module"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, default="BookOpen")
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lessons = relationship("LearningLesson", back_populates="module", cascade="all, delete-orphan",
                           order_by="LearningLesson.order")


class LearningLesson(Base):
    """A lesson within a module (e.g., 'Kremlin Origins')"""
    __tablename__ = "learning_lesson"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("learning_module.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    xp_reward = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    module = relationship("LearningModule", back_populates="lessons")
    questions = relationship("LearningQuestion", back_populates="lesson", cascade="all, delete-orphan",
                             order_by="LearningQuestion.order")
    user_progress = relationship("UserLessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    sessions = relationship("LearningSession", back_populates="lesson", cascade="all, delete-orphan")


class LearningQuestion(Base):
    """A question within a lesson"""
    __tablename__ = "learning_question"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("learning_lesson.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False, default="multiple_choice")  # multiple_choice, true_false, fill_blank
    options = Column(JSON, nullable=True)  # list of option strings
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    order = Column(Integer, default=0)

    # Relationships
    lesson = relationship("LearningLesson", back_populates="questions")
    history = relationship("UserQuestionHistory", back_populates="question", cascade="all, delete-orphan")


class UserLearningProgress(Base):
    """Overall learning progress for a user (Duolingo-like stats)"""
    __tablename__ = "user_learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_xp = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    daily_goal = Column(Integer, default=10)  # XP per day goal
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    league = Column(String, default="bronze")  # bronze, silver, gold, platinum, diamond

    # Relationships
    user = relationship("User", backref="learning_progress")


class UserLessonProgress(Base):
    """Per-lesson progress for a user"""
    __tablename__ = "user_lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("learning_lesson.id", ondelete="CASCADE"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False)
    best_score = Column(Integer, default=0)  # percentage 0-100
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="lesson_progress")
    lesson = relationship("LearningLesson", back_populates="user_progress")


class UserQuestionHistory(Base):
    """History of user answers to questions"""
    __tablename__ = "user_question_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("learning_question.id", ondelete="CASCADE"), nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="question_history")
    question = relationship("LearningQuestion", back_populates="history")


class LearningSession(Base):
    """A single learning session (attempt at a lesson)"""
    __tablename__ = "learning_session"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("learning_lesson.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Integer, default=0)  # percentage 0-100
    xp_earned = Column(Integer, default=0)

    # Relationships
    user = relationship("User", backref="learning_sessions")
    lesson = relationship("LearningLesson", back_populates="sessions")
