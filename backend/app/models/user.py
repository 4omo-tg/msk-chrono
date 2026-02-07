from sqlalchemy import Column, Integer, String, Boolean, Float, BigInteger
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
    
    # Gamification
    level = Column(Integer, default=1)
    xp = Column(Float, default=0.0)
    bio = Column(String, nullable=True)
    
    # Relationships
    achievements = relationship("UserAchievement", back_populates="user")
