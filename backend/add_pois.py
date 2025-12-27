import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route
from app.models.poi import PointOfInterest
from sqlalchemy import select

async def add_pois():
    async with AsyncSessionLocal() as session:
        # Find the route
        result = await session.execute(select(Route).where(Route.title == "Прогулка по Красной площади"))
        route = result.scalars().first()
        
        # Fallback to English title if not found (in case previous update failed silently or something)
        if not route:
            result = await session.execute(select(Route).where(Route.title == "Red Square Tour"))
            route = result.scalars().first()

        if not route:
            print("Route not found!")
            return

        print(f"Adding points to route: {route.title}")

        # Create new POIs
        gum = PointOfInterest(
            title="ГУМ",
            description="Главный Универсальный Магазин — памятник архитектуры и роскошный торговый центр.",
            latitude=55.7546,
            longitude=37.6215
        )
        
        history_museum = PointOfInterest(
            title="Государственный исторический музей",
            description="Крупнейший национальный исторический музей России.",
            latitude=55.7553,
            longitude=37.6178
        )
        
        zaryadye = PointOfInterest(
            title="Парк Зарядье",
            description="Природно-ландшафтный парк с уникальным Парящим мостом.",
            latitude=55.7510,
            longitude=37.6276
        )

        session.add_all([gum, history_museum, zaryadye])
        
        # Add to route
        # Since it's a list, we can append
        # Note: SQLAlchemy async relationship loading can be tricky. 
        # Ideally we should load route with options(selectinload(Route.points))
        # But here we are just adding to the collection.
        # Let's try appending directly if the relationship is loaded or simple append works.
        # safely we can assume we need to fetch items first or just append to the list if we know it works.
        # Actually, let's try to just fetch the poi list first to be safe, or simply append.
        # Async session might complain if we touch lazy loaded attribut without loading.
        
        # Re-fetching route with eager load might be safer, but let's try assuming standard behavior for now:
        # We can just add objects and commit, managing the association manually if needed, 
        # BUT for M2M simpler to just: route.points.append(new_poi)
        # However, await route.awaitable_attrs.points.append() might be needed in some configs.
        # Given the config is simple, I'll try straightforward append. 
        
        # A safer way in async without loading everything is adding to the session and letting commit handle simple inserts if mapped correctly. 
        # But let's try to access the collection. If it's not loaded, it will raise.
        
        # Let's retry with explicit loading just in case
        pass

    # Re-open session to do it cleanly with loading
    from sqlalchemy.orm import selectinload
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Route).options(selectinload(Route.points)).where(Route.id == route.id)
        )
        route_loaded = result.scalars().first()
        
        route_loaded.points.append(gum)
        route_loaded.points.append(history_museum)
        route_loaded.points.append(zaryadye)
        
        await session.commit()
        print("POIs added successfully.")

if __name__ == "__main__":
    asyncio.run(add_pois())
