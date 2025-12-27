from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserProgressBase(BaseModel):
    status: str
    completed_points_count: int = 0

class UserProgressCreate(UserProgressBase):
    route_id: int
    status: str = "started"

class UserProgressUpdate(BaseModel):
    status: Optional[str] = None
    completed_points_count: Optional[int] = None

class UserProgressInDBBase(UserProgressBase):
    id: int
    user_id: int
    route_id: int

    model_config = ConfigDict(from_attributes=True)

class UserProgress(UserProgressInDBBase):
    pass

class CheckIn(BaseModel):
    poi_id: int
    route_id: int

class CheckInResponse(BaseModel):
    updated_progress: UserProgress
    xp_gained: float
    new_total_xp: float
    new_level: int
