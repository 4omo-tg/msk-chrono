import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route
from app.models.poi import PointOfInterest as POI
from sqlalchemy import select

async def update_route():
    async with AsyncSessionLocal() as session:
        # Find the Red Square Tour route
        result = await session.execute(select(Route).where(Route.title == "Red Square Tour"))
        route = result.scalars().first()
        
        if route:
            route.title = "Прогулка по Красной площади"
            route.description = "Историческая прогулка по сердцу Москвы с посещением Кремля и собора Василия Блаженного."
            route.difficulty = "easy" # Kept as code value, but UI maps it
            
            # Update POIs associated with this route if possible, but POIs are separate objects in my model potentially?
            # Let's check POIs.
            # In the previous curl, POIs were created with the route.
            # Let's just update the route for now.
            
            session.add(route)
            await session.commit()
            print("Route updated successfully.")
        else:
            print("Route not found.")

        # Update POIs
        result = await session.execute(select(POI))
        pois = result.scalars().all()
        for poi in pois:
            if "St. Basil" in poi.title:
                poi.title = "Собор Василия Блаженного"
                poi.description = "Знаменитый собор с разноцветными куполами."
                session.add(poi)
            elif "Lenin" in poi.title:
                poi.title = "Мавзолей Ленина"
                poi.description = "Усыпальница Владимира Ленина."
                session.add(poi)
        
        await session.commit()
        print("POIs updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_route())
