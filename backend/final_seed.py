import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route, route_poi_association
from app.models.poi import PointOfInterest as POI
from sqlalchemy import delete, select

async def final_seed():
    async with AsyncSessionLocal() as session:
        # Clear existing routes and associations (M2M table)
        # Note: In SQLite without cascading, we might need to be careful.
        # But we want to keep the POIs if possible or just rebuild them.
        # Let's rebuild everything for a clean state.
        await session.execute(delete(route_poi_association))
        await session.execute(delete(Route))
        await session.execute(delete(POI))
        
        print("Cleared database.")

        # Create POIs in order
        points_data = [
            ("Государственный исторический музей", "Крупнейший национальный исторический музей России.", 55.7553, 37.6178),
            ("Мавзолей Ленина", "Усыпальница Владимира Ленина на Красной площади.", 55.7537, 37.6198),
            ("ГУМ", "Главный Универсальный Магазин — шедевр архитектуры псевдорусского стиля.", 55.7546, 37.6215),
            ("Собор Василия Блаженного", "Знаменитый собор с яркими куполами, символ Москвы.", 55.7525, 37.6231),
            ("Парк Зарядье", "Современный парк с панорамными видами и Парящим мостом.", 55.7510, 37.6276)
        ]
        
        points = []
        for title, desc, lat, lon in points_data:
            poi = POI(title=title, description=desc, latitude=lat, longitude=lon)
            points.append(poi)
            session.add(poi)

        # Create the Route
        route = Route(
            title="Сердце Москвы",
            description="Кольцевой маршрут по самым знаковым местам центра столицы.",
            difficulty="easy",
            reward_xp=150,
            is_premium=False
        )
        
        # Link points to route
        for poi in points:
            route.points.append(poi)
            
        session.add(route)
        await session.commit()
        print("Route 'Сердце Москвы' created with 5 points.")

if __name__ == "__main__":
    asyncio.run(final_seed())
