from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    username: Optional[str] = None
    bio: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    display_name: Optional[str] = None
    profile_visibility: Optional[str] = None
    show_on_leaderboard: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# Profile customization update
class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    equipped_title_id: Optional[int] = None
    equipped_frame_id: Optional[int] = None
    equipped_badge_ids: Optional[List[int]] = None  # Max 3 badges
    profile_background: Optional[str] = None
    profile_visibility: Optional[str] = None
    show_on_leaderboard: Optional[bool] = None


# Telegram auth data
class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class UserInDBBase(UserBase):
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None
    telegram_photo_url: Optional[str] = None

    class Config:
        from_attributes = True


# Title schema
class TitleOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    color: str
    rarity: str
    
    class Config:
        from_attributes = True


# Frame schema
class FrameOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    image_url: Optional[str]
    css_class: Optional[str]
    rarity: str
    
    class Config:
        from_attributes = True


# Badge schema
class BadgeOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    icon: str
    color: str
    rarity: str
    
    class Config:
        from_attributes = True


# Additional properties to return via API
class User(UserInDBBase):
    level: int = 1
    xp: float = 0.0
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_background: Optional[str] = None
    total_distance_km: float = 0.0
    total_time_minutes: int = 0
    streak_days: int = 0
    reputation: int = 0
    chrono_crystals: int = 5
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    profile_visibility: str = "public"
    show_on_leaderboard: bool = True
    created_at: Optional[datetime] = None
    
    # Equipped cosmetics
    equipped_title_id: Optional[int] = None
    equipped_frame_id: Optional[int] = None
    equipped_badge_ids: Optional[str] = None


# Extended user profile with cosmetics
class UserProfile(User):
    equipped_title: Optional[TitleOut] = None
    equipped_frame: Optional[FrameOut] = None
    equipped_badges: List[BadgeOut] = []
    unlocked_titles_count: int = 0
    unlocked_frames_count: int = 0
    unlocked_badges_count: int = 0
    friends_count: int = 0
    achievements_count: int = 0


# Public profile (limited info)
class PublicProfile(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    level: int
    xp: float
    reputation: int
    profile_background: Optional[str] = None
    equipped_title: Optional[TitleOut] = None
    equipped_frame: Optional[FrameOut] = None
    equipped_badges: List[BadgeOut] = []
    achievements_count: int = 0
    friends_count: int = 0
    total_distance_km: float = 0.0
    streak_days: int = 0
    created_at: Optional[datetime] = None
    is_friend: bool = False
    friend_request_sent: bool = False
    friend_request_received: bool = False
    
    class Config:
        from_attributes = True


# User search result
class UserSearchResult(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    level: int
    equipped_title: Optional[TitleOut] = None
    equipped_frame: Optional[FrameOut] = None
    is_friend: bool = False
    
    class Config:
        from_attributes = True


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: Optional[str] = None
