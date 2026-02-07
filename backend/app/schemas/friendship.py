from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class FriendRequestCreate(BaseModel):
    to_user_id: int


class FriendRequestOut(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None
    
    # Include user info
    from_user_username: Optional[str] = None
    from_user_display_name: Optional[str] = None
    from_user_avatar_url: Optional[str] = None
    from_user_level: Optional[int] = None
    
    to_user_username: Optional[str] = None
    to_user_display_name: Optional[str] = None
    to_user_avatar_url: Optional[str] = None
    to_user_level: Optional[int] = None
    
    class Config:
        orm_mode = True


class FriendOut(BaseModel):
    id: int
    user_id: int
    friend_id: int
    created_at: datetime
    nickname: Optional[str] = None
    
    # Friend info
    friend_username: str
    friend_display_name: Optional[str] = None
    friend_avatar_url: Optional[str] = None
    friend_level: int
    friend_xp: float
    friend_is_online: bool = False  # TODO: implement online status
    
    class Config:
        orm_mode = True


class FriendshipUpdate(BaseModel):
    nickname: Optional[str] = None
