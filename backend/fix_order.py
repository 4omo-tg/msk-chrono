import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route, route_poi_association
from app.models.poi import PointOfInterest as POI
from sqlalchemy import select, delete

async def reorder_route():
    async with AsyncSessionLocal() as session:
        # 1. Fetch the route and points
        result = await session.execute(
            select(Route).where(Route.title == "Сердце Москвы")
        )
        route = result.scalars().first()
        if not route:
            print("Route not found")
            return

        # 2. Get current association to clean up (easiest way is to wipe associations for this route and re-add in order)
        # But we need to know WHICH points.
        # Let's fetch the points we care about by title.
        
        target_titles = [
            "Старый Каменный мост",
            "Румянцевский музей (Дом Пашкова)",
            "Боровицкая башня",
            "Государственный исторический музей",
            "Мавзолей Ленина",
            "ГУМ",
            "Собор Василия Блаженного",
            "Парк Зарядье"
        ]
        
        # We need to find the POI objects
        points_map = {}
        for title in target_titles:
            p_res = await session.execute(select(POI).where(POI.title == title))
            p = p_res.scalars().first()
            if p:
                points_map[title] = p
            else:
                print(f"Warning: POI {title} not found")

        # 3. Clear current points association for this route
        # Route.points is an instrumented list.
        # Clearing it should delete associations in the link table.
        # But we need to load it first.
        await session.refresh(route, attribute_names=['points'])
        route.points.clear()
        
        # 4. Add points back in correct order
        for title in target_titles:
            if title in points_map:
                route.points.append(points_map[title])
        
        await session.commit()
        print("Route reordered successfully.")

if __name__ == "__main__":
    asyncio.run(reorder_route())
