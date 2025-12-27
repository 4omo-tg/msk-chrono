from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Quiz(Base):
    """Quiz question for a POI"""
    __tablename__ = "quiz"
    
    id = Column(Integer, primary_key=True, index=True)
    poi_id = Column(Integer, ForeignKey("point_of_interest.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)  # "A", "B", "C", or "D"
    xp_reward = Column(Float, default=10.0)
    
    # Relationships
    poi = relationship("PointOfInterest", backref="quizzes")
    user_progress = relationship("UserQuizProgress", back_populates="quiz", cascade="all, delete-orphan")
