from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base_class import Base


class SiteSetting(Base):
    """Key-value store for runtime-editable settings (API tokens, etc.)"""
    __tablename__ = "sitesetting"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String, nullable=False, default="")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
