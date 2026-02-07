"""Cosmetic items: Titles, Frames, Badges"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Title(Base):
    """Титулы - отображаются под именем пользователя"""
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)  # "Исследователь", "Историк", etc
    description = Column(String, nullable=True)
    color = Column(String, default="amber")  # CSS color class
    rarity = Column(String, default="common")  # common, rare, epic, legendary
    
    # Unlock condition
    unlock_type = Column(String, nullable=False)  # 'achievement', 'level', 'special', 'purchase'
    unlock_value = Column(String, nullable=True)  # achievement_code or level number
    
    is_default = Column(Boolean, default=False)  # Доступен всем


class UserTitle(Base):
    """Разблокированные титулы пользователя"""
    __tablename__ = "user_title"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    title_id = Column(Integer, ForeignKey("title.id"), nullable=False)
    unlocked_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="unlocked_titles")
    title = relationship("Title")


class ProfileFrame(Base):
    """Рамки профиля - вокруг аватара"""
    __tablename__ = "profileframe"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)  # URL картинки рамки
    css_class = Column(String, nullable=True)  # CSS класс для рамки
    rarity = Column(String, default="common")
    
    # Unlock condition
    unlock_type = Column(String, nullable=False)  # 'level', 'achievement', 'special'
    unlock_value = Column(String, nullable=True)
    
    is_default = Column(Boolean, default=False)


class UserFrame(Base):
    """Разблокированные рамки пользователя"""
    __tablename__ = "user_frame"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    frame_id = Column(Integer, ForeignKey("profileframe.id"), nullable=False)
    unlocked_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="unlocked_frames")
    frame = relationship("ProfileFrame")


class Badge(Base):
    """Бейджи - мини-иконки для профиля (макс 3 отображаются)"""
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=False)  # Lucide icon name
    color = Column(String, default="amber")  # CSS color
    rarity = Column(String, default="common")
    
    # Unlock condition
    unlock_type = Column(String, nullable=False)
    unlock_value = Column(String, nullable=True)
    
    is_default = Column(Boolean, default=False)


class UserBadge(Base):
    """Разблокированные бейджи пользователя"""
    __tablename__ = "user_badge"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey("badge.id"), nullable=False)
    unlocked_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="unlocked_badges")
    badge = relationship("Badge")
