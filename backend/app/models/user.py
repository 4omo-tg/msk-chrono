from sqlalchemy import Column, Integer, String, Boolean, Float, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)  # nullable for telegram-only users
    hashed_password = Column(String, nullable=True)  # nullable for telegram-only users
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    
    # Telegram auth
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    telegram_username = Column(String, nullable=True)
    telegram_first_name = Column(String, nullable=True)
    telegram_photo_url = Column(String, nullable=True)
    
    # Profile customization
    display_name = Column(String, nullable=True)  # Отображаемый ник (может отличаться от username)
    avatar_url = Column(String, nullable=True)  # Своя фотка профиля
    bio = Column(String, nullable=True)
    
    # Equipped cosmetics
    equipped_title_id = Column(Integer, ForeignKey("title.id"), nullable=True)
    equipped_frame_id = Column(Integer, ForeignKey("profileframe.id"), nullable=True)
    equipped_badge_ids = Column(String, nullable=True)  # JSON array of badge IDs (max 3)
    profile_background = Column(String, default="default")  # Background style
    
    # Gamification
    level = Column(Integer, default=1)
    xp = Column(Float, default=0.0)
    total_distance_km = Column(Float, default=0.0)  # Общая дистанция
    total_time_minutes = Column(Integer, default=0)  # Общее время прогулок
    streak_days = Column(Integer, default=0)  # Дни подряд
    last_activity_date = Column(DateTime, nullable=True)  # Для подсчёта streak
    reputation = Column(Integer, default=0)  # Репутация от других игроков
    
    # Privacy settings
    profile_visibility = Column(String, default="public")  # public, friends, private
    show_on_leaderboard = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    achievements = relationship("UserAchievement", back_populates="user")
    equipped_title = relationship("Title", foreign_keys=[equipped_title_id])
    equipped_frame = relationship("ProfileFrame", foreign_keys=[equipped_frame_id])
    unlocked_titles = relationship("UserTitle", back_populates="user")
    unlocked_frames = relationship("UserFrame", back_populates="user")
    unlocked_badges = relationship("UserBadge", back_populates="user")
