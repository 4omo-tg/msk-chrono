from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Quiz Schemas
class QuizBase(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str  # "A", "B", "C", or "D"
    xp_reward: float = 10.0
    poi_id: int

class QuizCreate(QuizBase):
    pass

class QuizUpdate(BaseModel):
    question: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    xp_reward: Optional[float] = None
    poi_id: Optional[int] = None

class Quiz(QuizBase):
    id: int
    
    class Config:
        from_attributes = True

# For frontend - hide correct answer
class QuizPublic(BaseModel):
    id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    xp_reward: float
    poi_id: int
    
    class Config:
        from_attributes = True

# Quiz submission
class QuizSubmit(BaseModel):
    answer: str  # "A", "B", "C", or "D"

class QuizSubmitResponse(BaseModel):
    is_correct: bool
    xp_earned: float
    correct_answer: str
    new_total_xp: float
    new_level: int

# User Quiz Progress
class UserQuizProgressBase(BaseModel):
    user_id: int
    quiz_id: int
    is_correct: bool

class UserQuizProgress(UserQuizProgressBase):
    id: int
    completed_at: datetime
    
    class Config:
        from_attributes = True
