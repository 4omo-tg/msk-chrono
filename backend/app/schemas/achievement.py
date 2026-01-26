from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AchievementBase(BaseModel):
    code: str
    title: str
    description: str
    icon: str = "Award"
    xp_reward: int = 0
    condition_type: str  # 'points', 'routes', 'level'
    condition_value: int


class Achievement(AchievementBase):
    id: int
    
    class Config:
        from_attributes = True


class AchievementCreate(AchievementBase):
    pass


class UserAchievementBase(BaseModel):
    achievement_id: int


class UserAchievement(UserAchievementBase):
    id: int
    user_id: int
    unlocked_at: datetime
    achievement: Achievement
    
    class Config:
        from_attributes = True


class AchievementWithStatus(Achievement):
    """Achievement with unlock status for current user"""
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None


class NewAchievementsResponse(BaseModel):
    """Response when new achievements are unlocked"""
    new_achievements: List[Achievement]
    xp_gained: float
