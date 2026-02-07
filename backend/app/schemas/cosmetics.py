from typing import Optional
from datetime import datetime
from pydantic import BaseModel


# Title schemas
class TitleBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    color: str = "amber"
    rarity: str = "common"
    unlock_type: str
    unlock_value: Optional[str] = None
    is_default: bool = False


class TitleOut(TitleBase):
    id: int
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


# Frame schemas
class FrameBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    css_class: Optional[str] = None
    rarity: str = "common"
    unlock_type: str
    unlock_value: Optional[str] = None
    is_default: bool = False


class FrameOut(FrameBase):
    id: int
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


# Badge schemas
class BadgeBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    icon: str
    color: str = "amber"
    rarity: str = "common"
    unlock_type: str
    unlock_value: Optional[str] = None
    is_default: bool = False


class BadgeOut(BadgeBase):
    id: int
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


# Equip request
class EquipTitle(BaseModel):
    title_id: Optional[int] = None  # None to unequip


class EquipFrame(BaseModel):
    frame_id: Optional[int] = None


class EquipBadges(BaseModel):
    badge_ids: list[int] = []  # Max 3
