from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ---------- POI Photo (by year) ----------

class POIPhotoBase(BaseModel):
    year: int
    image_url: str
    description: Optional[str] = None
    source: Optional[str] = None

class POIPhotoCreate(POIPhotoBase):
    pass

class POIPhoto(POIPhotoBase):
    id: int
    poi_id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- POI ----------

class PointOfInterestBase(BaseModel):
    title: str
    description: Optional[str] = None
    address: Optional[str] = None
    full_article: Optional[str] = None
    historic_image_url: Optional[str] = None
    modern_image_url: Optional[str] = None
    historic_images: Optional[List[str]] = []
    modern_images: Optional[List[str]] = []
    historic_panorama_url: Optional[str] = None
    modern_panorama_url: Optional[str] = None
    latitude: float
    longitude: float

class PointOfInterestCreate(PointOfInterestBase):
    photos: Optional[List[POIPhotoCreate]] = []

class PointOfInterestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    full_article: Optional[str] = None
    historic_image_url: Optional[str] = None
    modern_image_url: Optional[str] = None
    historic_images: Optional[List[str]] = None
    modern_images: Optional[List[str]] = None
    historic_panorama_url: Optional[str] = None
    modern_panorama_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photos: Optional[List[POIPhotoCreate]] = None

class PointOfInterestInDBBase(PointOfInterestBase):
    id: int
    photos: List[POIPhoto] = []
    model_config = ConfigDict(from_attributes=True)

class PointOfInterest(PointOfInterestInDBBase):
    pass
