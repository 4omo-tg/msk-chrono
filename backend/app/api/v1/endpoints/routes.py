from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.api import deps
# from geoalchemy2.shape import to_shape

router = APIRouter()


def poi_to_schema(p: models.PointOfInterest) -> schemas.PointOfInterest:
    """Convert POI model to schema with all fields."""
    photos = []
    if hasattr(p, 'photos') and p.photos:
        photos = [schemas.POIPhoto.model_validate(ph) for ph in p.photos]
    return schemas.PointOfInterest(
        id=p.id,
        title=p.title,
        description=p.description,
        address=p.address,
        full_article=p.full_article,
        historic_image_url=p.historic_image_url,
        modern_image_url=p.modern_image_url,
        historic_images=p.historic_images or [],
        modern_images=p.modern_images or [],
        historic_panorama_url=p.historic_panorama_url,
        modern_panorama_url=p.modern_panorama_url,
        latitude=p.latitude,
        longitude=p.longitude,
        photos=photos,
    )

@router.get("", response_model=List[schemas.Route])
async def read_routes(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve routes.
    """
    # Eager load points
    result = await db.execute(
        select(models.Route)
        .options(
            selectinload(models.Route.points)
            .selectinload(models.PointOfInterest.photos)
        )
        .offset(skip)
        .limit(limit)
    )
    routes = result.scalars().all()
    
    # We need to map the POIs inside to schema POIs with lat/lon
    route_schemas = []
    for r in routes:
        points_schema = [poi_to_schema(p) for p in r.points]
            
        route_schemas.append(
            schemas.Route(
                id=r.id,
                title=r.title,
                description=r.description,
                difficulty=r.difficulty,
                reward_xp=r.reward_xp,
                is_premium=r.is_premium,
                points=points_schema
            )
        )
    return route_schemas

@router.post("", response_model=schemas.Route)
async def create_route(
    *,
    db: AsyncSession = Depends(deps.get_db),
    route_in: schemas.RouteCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new route. Only superusers.
    """
    route = models.Route(
        title=route_in.title,
        description=route_in.description,
        difficulty=route_in.difficulty,
        reward_xp=route_in.reward_xp,
        is_premium=route_in.is_premium
    )
    
    # First add route to get an ID
    db.add(route)
    await db.flush()  # Get route.id without committing
    
    if route_in.poi_ids:
        # Manually insert into association table with order preserved
        from sqlalchemy import insert
        for idx, poi_id in enumerate(route_in.poi_ids):
            stmt = insert(models.route_poi_association).values(
                route_id=route.id,
                poi_id=poi_id,
                order=idx
            )
            await db.execute(stmt)

    await db.commit()
    await db.refresh(route, attribute_names=['points']) # refresh relationships
    
    points_schema = [poi_to_schema(p) for p in route.points]

    return schemas.Route(
        id=route.id,
        title=route.title,
        description=route.description,
        difficulty=route.difficulty,
        reward_xp=route.reward_xp,
        is_premium=route.is_premium,
        points=points_schema
    )

@router.get("/{route_id}", response_model=schemas.Route)
async def read_route(
    *,
    db: AsyncSession = Depends(deps.get_db),
    route_id: int,
) -> Any:
    """
    Get route by ID.
    """
    result = await db.execute(
        select(models.Route)
        .options(
            selectinload(models.Route.points)
            .selectinload(models.PointOfInterest.photos)
        )
        .where(models.Route.id == route_id)
    )
    route = result.scalars().first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    points_schema = [poi_to_schema(p) for p in route.points]

    return schemas.Route(
        id=route.id,
        title=route.title,
        description=route.description,
        difficulty=route.difficulty,
        reward_xp=route.reward_xp,
        is_premium=route.is_premium,
        points=points_schema
    )

@router.put("/{route_id}", response_model=schemas.Route)
async def update_route(
    *,
    db: AsyncSession = Depends(deps.get_db),
    route_id: int,
    route_in: schemas.RouteUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update route. Only superusers.
    """
    # Fetch route with points
    result = await db.execute(
        select(models.Route)
        .options(selectinload(models.Route.points))
        .where(models.Route.id == route_id)
    )
    route = result.scalars().first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    update_data = route_in.model_dump(exclude_unset=True)
    
    # Handle POI association update
    if "poi_ids" in update_data:
        poi_ids = update_data.pop("poi_ids")
        if poi_ids is not None:
            # Delete existing associations
            from sqlalchemy import delete, insert
            delete_stmt = delete(models.route_poi_association).where(
                models.route_poi_association.c.route_id == route_id
            )
            await db.execute(delete_stmt)
            
            # Insert new associations with order
            for idx, poi_id in enumerate(poi_ids):
                insert_stmt = insert(models.route_poi_association).values(
                    route_id=route_id,
                    poi_id=poi_id,
                    order=idx
                )
                await db.execute(insert_stmt)

    for field, value in update_data.items():
        setattr(route, field, value)

    db.add(route)
    await db.commit()
    await db.refresh(route, attribute_names=['points'])
    
    points_schema = [poi_to_schema(p) for p in route.points]

    return schemas.Route(
        id=route.id,
        title=route.title,
        description=route.description,
        difficulty=route.difficulty,
        reward_xp=route.reward_xp,
        is_premium=route.is_premium,
        points=points_schema
    )

@router.delete("/{route_id}", response_model=schemas.Route)
async def delete_route(
    *,
    db: AsyncSession = Depends(deps.get_db),
    route_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete route. Only superusers.
    """
    # Fetch route with points and photos to return schema
    result = await db.execute(
        select(models.Route)
        .options(
            selectinload(models.Route.points)
            .selectinload(models.PointOfInterest.photos)
        )
        .where(models.Route.id == route_id)
    )
    route = result.scalars().first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    points_schema = [poi_to_schema(p) for p in route.points]
    
    route_schema = schemas.Route(
        id=route.id,
        title=route.title,
        description=route.description,
        difficulty=route.difficulty,
        reward_xp=route.reward_xp,
        is_premium=route.is_premium,
        points=points_schema
    )

    # Delete via SQL to avoid lazy-load / MissingGreenlet issues
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(models.route_poi_association).where(
            models.route_poi_association.c.route_id == route_id
        )
    )
    await db.execute(
        sql_delete(models.UserProgress).where(
            models.UserProgress.route_id == route_id
        )
    )
    await db.execute(
        sql_delete(models.Route).where(models.Route.id == route_id)
    )
    await db.commit()
    return route_schema
