from sqlalchemy import Column, Integer, String, Float, Text
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
    
    historic_image_url = Column(String, nullable=True)
    modern_image_url = Column(String, nullable=True)
