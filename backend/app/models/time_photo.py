from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class TimePhoto(Base):
    __tablename__ = "time_photo"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    original_image_url = Column(String, nullable=False)
    result_image_url = Column(String, nullable=True)
    target_year = Column(Integer, nullable=False)
    apply_era_style = Column(Boolean, server_default="true", nullable=False)
    style_applied = Column(String, nullable=True)
    prompt_used = Column(String, nullable=True)
    geminigen_uuid = Column(String, nullable=True)
    status = Column(String, server_default="pending", nullable=False)
    error_message = Column(String, nullable=True)
    cost = Column(Integer, server_default="1", nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="time_photos")
