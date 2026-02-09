from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.PointOfInterest])
async def read_pois(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Any:
    query = select(models.PointOfInterest).options(selectinload(models.PointOfInterest.photos))
    if latitude is not None and longitude is not None:
        delta = 0.01
        query = query.where(
            models.PointOfInterest.latitude.between(latitude - delta, latitude + delta),
            models.PointOfInterest.longitude.between(longitude - delta, longitude + delta),
        )
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{poi_id}", response_model=schemas.PointOfInterest)
async def read_poi(*, db: AsyncSession = Depends(deps.get_db), poi_id: int) -> Any:
    result = await db.execute(
        select(models.PointOfInterest)
        .options(selectinload(models.PointOfInterest.photos))
        .where(models.PointOfInterest.id == poi_id)
    )
    poi = result.scalars().first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi


@router.post("/", response_model=schemas.PointOfInterest)
async def create_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poi_in: schemas.PointOfInterestCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    data = poi_in.model_dump(exclude={"photos"})
    poi = models.PointOfInterest(**data)
    db.add(poi)
    await db.flush()
    for p in (poi_in.photos or []):
        db.add(models.POIPhoto(poi_id=poi.id, **p.model_dump()))
    await db.commit()
    return await read_poi(db=db, poi_id=poi.id)


@router.put("/{poi_id}", response_model=schemas.PointOfInterest)
async def update_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poi_id: int,
    poi_in: schemas.PointOfInterestUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    result = await db.execute(
        select(models.PointOfInterest)
        .options(selectinload(models.PointOfInterest.photos))
        .where(models.PointOfInterest.id == poi_id)
    )
    poi = result.scalars().first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    update_data = poi_in.model_dump(exclude_unset=True, exclude={"photos"})
    for field, value in update_data.items():
        setattr(poi, field, value)
    if poi_in.photos is not None:
        # Перезапись всех фото
        for old in poi.photos:
            await db.delete(old)
        await db.flush()
        for p in poi_in.photos:
            db.add(models.POIPhoto(poi_id=poi.id, **p.model_dump()))
    await db.commit()
    return await read_poi(db=db, poi_id=poi.id)


@router.delete("/{poi_id}")
async def delete_poi(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poi_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    poi = await db.get(models.PointOfInterest, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    await db.delete(poi)
    await db.commit()
    return {"ok": True}


# --- Article ---

@router.get("/{poi_id}/article")
async def get_article(poi_id: int, db: AsyncSession = Depends(deps.get_db)) -> Any:
    """Get the full article for a POI."""
    result = await db.execute(
        select(models.PointOfInterest).where(models.PointOfInterest.id == poi_id)
    )
    poi = result.scalars().first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return {
        "poi_id": poi.id,
        "title": poi.title,
        "address": poi.address,
        "description": poi.description,
        "full_article": poi.full_article,
    }


# --- Photo sub-resource ---

@router.get("/{poi_id}/photos", response_model=List[schemas.POIPhoto])
async def list_photos(
    poi_id: int,
    year: Optional[int] = None,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Get photos for a POI, optionally filtered by year."""
    q = select(models.POIPhoto).where(models.POIPhoto.poi_id == poi_id)
    if year is not None:
        q = q.where(models.POIPhoto.year == year)
    q = q.order_by(models.POIPhoto.year)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{poi_id}/years")
async def list_years(poi_id: int, db: AsyncSession = Depends(deps.get_db)) -> Any:
    """Get available years for a POI."""
    from sqlalchemy import distinct, func as f
    result = await db.execute(
        select(models.POIPhoto.year, f.count(models.POIPhoto.id))
        .where(models.POIPhoto.poi_id == poi_id)
        .group_by(models.POIPhoto.year)
        .order_by(models.POIPhoto.year)
    )
    return [{"year": row[0], "count": row[1]} for row in result.all()]


@router.post("/{poi_id}/photos", response_model=schemas.POIPhoto)
async def add_photo(
    poi_id: int,
    photo_in: schemas.POIPhotoCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    poi = await db.get(models.PointOfInterest, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    photo = models.POIPhoto(poi_id=poi_id, **photo_in.model_dump())
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


@router.delete("/{poi_id}/photos/{photo_id}")
async def delete_photo(
    poi_id: int,
    photo_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    photo = await db.get(models.POIPhoto, photo_id)
    if not photo or photo.poi_id != poi_id:
        raise HTTPException(status_code=404, detail="Photo not found")
    await db.delete(photo)
    await db.commit()
    return {"ok": True}
