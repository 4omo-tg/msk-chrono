import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def force_reorder():
    async with AsyncSessionLocal() as session:
        # Get route ID
        res = await session.execute(text("SELECT id FROM route WHERE title = 'Сердце Москвы'"))
        route_id = res.scalar()
        if not route_id:
            print("Route not found")
            return

        print(f"Route ID: {route_id}")

        # Get POI IDs map
        res = await session.execute(text("SELECT id, title FROM point_of_interest"))
        pois = {row.title: row.id for row in res}
        
        target_order = [
            "Старый Каменный мост",
            "Румянцевский музей (Дом Пашкова)",
            "Боровицкая башня",
            "Государственный исторический музей",
            "Мавзолей Ленина",
            "ГУМ",
            "Собор Василия Блаженного",
            "Парк Зарядье"
        ]

        # Explicitly delete associations
        await session.execute(text(f"DELETE FROM route_poi WHERE route_id = {route_id}"))
        
        # Explicitly insert in order
        for title in target_order:
            poi_id = pois.get(title)
            if poi_id:
                await session.execute(text(f"INSERT INTO route_poi (route_id, poi_id) VALUES ({route_id}, {poi_id})"))
                print(f"Inserted {title}")
            else:
                print(f"Missing POI: {title}")

        await session.commit()
        print("Force reorder complete.")

if __name__ == "__main__":
    asyncio.run(force_reorder())
