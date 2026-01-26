from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.dialects.postgresql import ARRAY
# from geoalchemy2 import Geometry
from app.db.base_class import Base

class PointOfInterest(Base):
    __tablename__ = "point_of_interest"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Geospatial data: Point(lon, lat)
    # Using simple Float for SQLite compatibility instead of PostGIS Geometry
    # location = Column(Geometry("POINT", srid=4326), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Legacy single image fields (kept for backwards compatibility)
    historic_image_url = Column(String, nullable=True)
    modern_image_url = Column(String, nullable=True)
    
    # Gallery - arrays of image URLs
    historic_images = Column(ARRAY(String), nullable=True, default=[])  # Массив исторических фото
    modern_images = Column(ARRAY(String), nullable=True, default=[])    # Массив современных фото
    
    # Panoramas
    historic_panorama_url = Column(String, nullable=True)  # Историческая панорама
    modern_panorama_url = Column(String, nullable=True)    # Современная панорама
