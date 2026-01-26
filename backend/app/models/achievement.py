from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Achievement(Base):
    """Achievement definition"""
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)  # e.g. 'first_step'
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String, nullable=False, default='Award')  # Lucide icon name
    xp_reward = Column(Integer, default=0)  # XP for unlocking
    
    # Conditions (JSON or simple fields)
    condition_type = Column(String, nullable=False)  # 'points', 'routes', 'level'
    condition_value = Column(Integer, nullable=False)  # threshold value


class UserAchievement(Base):
    """User's unlocked achievements"""
    __tablename__ = "user_achievement"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievement.id"), nullable=False)
    unlocked_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")
