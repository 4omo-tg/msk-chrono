from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class PointOfInterest(Base):
    __tablename__ = "point_of_interest"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)  # Адрес: "Красная площадь, 1"

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    full_article = Column(Text, nullable=True)    # Полная статья/история объекта (Markdown)

    # Legacy single image fields (kept for backwards compatibility)
    historic_image_url = Column(String, nullable=True)
    modern_image_url = Column(String, nullable=True)

    # Gallery - arrays of image URLs (legacy flat lists)
    historic_images = Column(ARRAY(String), nullable=True, default=[])
    modern_images = Column(ARRAY(String), nullable=True, default=[])

    # Panoramas
    historic_panorama_url = Column(String, nullable=True)
    modern_panorama_url = Column(String, nullable=True)

    # Relationships
    photos = relationship("POIPhoto", back_populates="poi", cascade="all, delete-orphan",
                          order_by="POIPhoto.year")


class POIPhoto(Base):
    """Фотография точки интереса, привязанная к конкретному году."""
    __tablename__ = "poi_photo"

    id = Column(Integer, primary_key=True, index=True)
    poi_id = Column(Integer, ForeignKey("point_of_interest.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)       # 1890, 1935, 2024 …
    image_url = Column(String, nullable=False)
    description = Column(String, nullable=True)               # подпись к фото
    source = Column(String, nullable=True)                    # источник / автор

    poi = relationship("PointOfInterest", back_populates="photos")
