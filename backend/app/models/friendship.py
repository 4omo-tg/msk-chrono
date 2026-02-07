"""Friendship system"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class FriendRequest(Base):
    """Заявки в друзья"""
    __tablename__ = "friend_request"
    
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, server_default=func.now())
    responded_at = Column(DateTime, nullable=True)
    
    from_user = relationship("User", foreign_keys=[from_user_id], backref="sent_friend_requests")
    to_user = relationship("User", foreign_keys=[to_user_id], backref="received_friend_requests")
    
    __table_args__ = (
        UniqueConstraint('from_user_id', 'to_user_id', name='unique_friend_request'),
    )


class Friendship(Base):
    """Установленные дружеские связи"""
    __tablename__ = "friendship"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    friend_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Дополнительные поля
    nickname = Column(String, nullable=True)  # Локальный ник для друга
    
    user = relationship("User", foreign_keys=[user_id], backref="friendships_as_user")
    friend = relationship("User", foreign_keys=[friend_id], backref="friendships_as_friend")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
    )
