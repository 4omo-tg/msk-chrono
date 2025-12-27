import asyncio
from app.db.session import AsyncSessionLocal
from app.models.route import Route
from app.models.poi import PointOfInterest as POI
from sqlalchemy import select

async def seed_db():
    async with AsyncSessionLocal() as session:
        # Check if route exists
        result = await session.execute(select(Route).where(Route.title == "Прогулка по Красной площади"))
        existing_route = result.scalars().first()
        
        if existing_route:
            print("Route already exists.")
            return

        print("Creating route and POIs...")

        # Create POIs
        st_basil = POI(
            title="Собор Василия Блаженного",
            description="Знаменитый собор с разноцветными куполами.",
            latitude=55.7525,
            longitude=37.6231
        )
        mausoleum = POI(
            title="Мавзолей Ленина",
            description="Усыпальница Владимира Ленина.",
            latitude=55.7537,
            longitude=37.6198
        )
        gum = POI(
            title="ГУМ",
            description="Главный Универсальный Магазин — памятник архитектуры.",
            latitude=55.7546,
            longitude=37.6215
        )
        history_museum = POI(
            title="Государственный исторический музей",
            description="Крупнейший национальный исторический музей России.",
            latitude=55.7553,
            longitude=37.6178
        )
        zaryadye = POI(
            title="Парк Зарядье",
            description="Природно-ландшафтный парк с уникальным Парящим мостом.",
            latitude=55.7510,
            longitude=37.6276
        )

        # Create Route
        route = Route(
            title="Прогулка по Красной площади",
            description="Историческая прогулка по сердцу Москвы.",
            difficulty="easy",
            reward_xp=100,
            is_premium=False
        )
        
        # Add everything to session first to get IDs (though logic might handle it)
        # Better to append to route.points directly
        route.points.append(st_basil)
        route.points.append(mausoleum)
        route.points.append(gum)
        route.points.append(history_museum)
        route.points.append(zaryadye)
        
        session.add(route)
        await session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_db())
