from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps

router = APIRouter()


def poi_to_schema(poi: models.PointOfInterest) -> schemas.PointOfInterest:
    """Convert POI model to schema with all fields."""
    return schemas.PointOfInterest(
        id=poi.id,
        title=poi.title,
        description=poi.description,
        historic_image_url=poi.historic_image_url,
        modern_image_url=poi.modern_image_url,
        historic_images=poi.historic_images or [],
        modern_images=poi.modern_images or [],
        historic_panorama_url=poi.historic_panorama_url,
        modern_panorama_url=poi.modern_panorama_url,
        latitude=poi.latitude,
        longitude=poi.longitude
    )


@router.get("/", response_model=List[schemas.PointOfInterest])
async def read_pois(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[float] = 500,
) -> Any:
    """
    Retrieve POIs. Filter by nearby if lat/lon/radius provided.
    """
    query = select(models.PointOfInterest)
    
    if latitude is not None and longitude is not None:
         delta = 0.01 
         query = query.where(
             models.PointOfInterest.latitude.between(latitude - delta, latitude + delta),
             models.PointOfInterest.longitude.between(longitude - delta, longitude + delta)
         )
    
    result = await db.execute(query.offset(skip).limit(limit))
    pois = result.scalars().all()
    
    return [poi_to_schema(poi) for poi in pois]


@router.post("/", response_model=schemas.PointOfInterest)
async def create_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poi_in: schemas.PointOfInterestCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new POI. Only superusers.
    """
    poi = models.PointOfInterest(
        title=poi_in.title,
        description=poi_in.description,
        historic_image_url=poi_in.historic_image_url,
        modern_image_url=poi_in.modern_image_url,
        historic_images=poi_in.historic_images or [],
        modern_images=poi_in.modern_images or [],
        historic_panorama_url=poi_in.historic_panorama_url,
        modern_panorama_url=poi_in.modern_panorama_url,
        latitude=poi_in.latitude,
        longitude=poi_in.longitude
    )
    db.add(poi)
    await db.commit()
    await db.refresh(poi)
    
    return poi_to_schema(poi)


@router.get("/{poi_id}", response_model=schemas.PointOfInterest)
async def read_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poi_id: int,
) -> Any:
    """
    Get POI by ID.
    """
    poi = await db.get(models.PointOfInterest, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    return poi_to_schema(poi)


@router.put("/{poi_id}", response_model=schemas.PointOfInterest)
async def update_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poi_id: int,
    poi_in: schemas.PointOfInterestUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update POI. Only superusers.
    """
    poi = await db.get(models.PointOfInterest, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    update_data = poi_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(poi, field, value)

    db.add(poi)
    await db.commit()
    await db.refresh(poi)
    
    return poi_to_schema(poi)


@router.delete("/{poi_id}", response_model=schemas.PointOfInterest)
async def delete_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poi_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete POI. Only superusers.
    """
    poi = await db.get(models.PointOfInterest, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
        
    poi_schema = poi_to_schema(poi)
    
    await db.delete(poi)
    await db.commit()
    return poi_schema
