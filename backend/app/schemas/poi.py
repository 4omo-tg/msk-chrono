from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class PointOfInterestBase(BaseModel):
    title: str
    description: Optional[str] = None
    historic_image_url: Optional[str] = None
    modern_image_url: Optional[str] = None
    # Gallery arrays
    historic_images: Optional[List[str]] = []
    modern_images: Optional[List[str]] = []
    # Panoramas
    historic_panorama_url: Optional[str] = None
    modern_panorama_url: Optional[str] = None
    # Location
    latitude: float
    longitude: float

class PointOfInterestCreate(PointOfInterestBase):
    pass

class PointOfInterestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    historic_image_url: Optional[str] = None
    modern_image_url: Optional[str] = None
    historic_images: Optional[List[str]] = None
    modern_images: Optional[List[str]] = None
    historic_panorama_url: Optional[str] = None
    modern_panorama_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PointOfInterestInDBBase(PointOfInterestBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class PointOfInterest(PointOfInterestInDBBase):
    pass
