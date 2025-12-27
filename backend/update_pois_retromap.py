import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route
from app.models.poi import PointOfInterest as POI
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def add_retromap_pois():
    async with AsyncSessionLocal() as session:
        # Find the main route
        result = await session.execute(
            select(Route).options(selectinload(Route.points)).where(Route.title == "Сердце Москвы")
        )
        route = result.scalars().first()
        
        if not route:
            print("Route 'Сердце Москвы' not found!")
            return

        print(f"Adding Retromap points to route: {route.title}")

        # Create new POIs
        pashkov = POI(
            title="Румянцевский музей (Дом Пашкова)",
            description="Один из красивейших особняков Москвы, на момент 1900 года — публичный музей.",
            latitude=55.7512,
            longitude=37.6125
        )
        
        borovitskaya = POI(
            title="Боровицкая башня",
            description="Проездная башня Московского Кремля, сохранившая свой исторический облик.",
            latitude=55.7502,
            longitude=37.6133
        )
        
        old_bridge = POI(
            title="Старый Каменный мост",
            description="Историческое местоположение и облик Всехсвятского каменного моста.",
            latitude=55.7485,
            longitude=37.6135
        )

        session.add_all([pashkov, borovitskaya, old_bridge])
        
        # Prepend to route points to start the walk here
        # points is a list, we can insert at the beginning
        route.points.insert(0, old_bridge)
        route.points.insert(1, pashkov)
        route.points.insert(2, borovitskaya)
        
        await session.commit()
        print("Retromap POIs added and linked successfully.")

if __name__ == "__main__":
    asyncio.run(add_retromap_pois())
