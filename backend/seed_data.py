import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import User, Route, PointOfInterest, Quiz, route_poi_association
from app.core.security import get_password_hash
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/moscow_chrono")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with AsyncSessionLocal() as db:
        # 1. Create admin user
        admin = User(
            email="admin@moscow.ru",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            level=10,
            xp=5000.0
        )
        db.add(admin)
        
        # 2. Create test user
        test_user = User(
            email="user@test.com",
            username="explorer",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            is_superuser=False,
            level=1,
            xp=0.0
        )
        db.add(test_user)
        
        # 3. Create POIs (Points of Interest)
        pois = [
            PointOfInterest(
                title="Красная площадь",
                description="Главная площадь России, расположенная в центре Москвы. Здесь проходили важнейшие события русской истории. Площадь возникла в конце XV века и первоначально называлась Торгом.",
                latitude=55.7539,
                longitude=37.6208,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Red_Square_Moscow.jpg/1200px-Red_Square_Moscow.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Red_Square_Moscow.jpg/1200px-Red_Square_Moscow.jpg"
            ),
            PointOfInterest(
                title="Храм Василия Блаженного",
                description="Православный храм, расположенный на Красной площади. Построен в 1555-1561 годах по приказу Ивана Грозного в честь взятия Казани. Один из самых узнаваемых символов России.",
                latitude=55.7525,
                longitude=37.6231,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Saint_Basil%27s_Cathedral_Moscow.jpg/800px-Saint_Basil%27s_Cathedral_Moscow.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Saint_Basil%27s_Cathedral_Moscow.jpg/800px-Saint_Basil%27s_Cathedral_Moscow.jpg"
            ),
            PointOfInterest(
                title="ГУМ",
                description="Крупный торговый комплекс в центре Москвы, занимающий целый квартал. Здание построено в 1890-1893 годах в псевдорусском стиле. Изначально назывался Верхние торговые ряды.",
                latitude=55.7546,
                longitude=37.6215,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Moscow_GUM.jpg/1200px-Moscow_GUM.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Moscow_GUM.jpg/1200px-Moscow_GUM.jpg"
            ),
            PointOfInterest(
                title="Мавзолей Ленина",
                description="Памятник-усыпальница на Красной площади у Кремлёвской стены. Построен в 1924-1930 годах. Здесь покоится тело Владимира Ильича Ленина.",
                latitude=55.7537,
                longitude=37.6198,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Lenin%27s_Mausoleum.jpg/800px-Lenin%27s_Mausoleum.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Lenin%27s_Mausoleum.jpg/800px-Lenin%27s_Mausoleum.jpg"
            ),
            PointOfInterest(
                title="Александровский сад",
                description="Парк в центре Москвы, расположенный вдоль западной Кремлёвской стены. Основан в 1821 году в честь победы над Наполеоном. Здесь находится Могила Неизвестного Солдата.",
                latitude=55.7520,
                longitude=37.6135,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Aleksandrovsky_Garden_Moscow.jpg/1200px-Aleksandrovsky_Garden_Moscow.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Aleksandrovsky_Garden_Moscow.jpg/1200px-Aleksandrovsky_Garden_Moscow.jpg"
            ),
            PointOfInterest(
                title="Большой театр",
                description="Один из крупнейших театров оперы и балета в мире. Основан в 1776 году. Современное здание построено в 1856 году в стиле классицизма.",
                latitude=55.7601,
                longitude=37.6186,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Bolshoi_Theatre.jpg/1200px-Bolshoi_Theatre.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Bolshoi_Theatre.jpg/1200px-Bolshoi_Theatre.jpg"
            ),
            PointOfInterest(
                title="Третьяковская галерея",
                description="Художественный музей, основанный в 1856 году купцом Павлом Третьяковым. Содержит одну из крупнейших в мире коллекций русского изобразительного искусства.",
                latitude=55.7415,
                longitude=37.6208,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Tretyakov_Gallery.jpg/1200px-Tretyakov_Gallery.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Tretyakov_Gallery.jpg/1200px-Tretyakov_Gallery.jpg"
            ),
            PointOfInterest(
                title="Арбат",
                description="Одна из старейших улиц Москвы, известная с XV века. Сегодня это пешеходная улица с множеством сувенирных магазинов, кафе и уличных артистов.",
                latitude=55.7520,
                longitude=37.5917,
                historic_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Arbat_street.jpg/1200px-Arbat_street.jpg",
                modern_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Arbat_street.jpg/1200px-Arbat_street.jpg"
            ),
        ]
        
        for poi in pois:
            db.add(poi)
        
        await db.flush()
        
        # 4. Create Routes
        route1 = Route(
            title="Сердце Москвы",
            description="Прогулка по главным достопримечательностям исторического центра столицы. Вы увидите Красную площадь, храм Василия Блаженного и другие знаковые места.",
            difficulty="easy",
            reward_xp=200.0,
            is_premium=False
        )
        db.add(route1)
        
        route2 = Route(
            title="Культурная Москва",
            description="Маршрут для ценителей искусства. Посетите Большой театр, Третьяковскую галерею и прогуляйтесь по историческому Арбату.",
            difficulty="medium",
            reward_xp=300.0,
            is_premium=False
        )
        db.add(route2)
        
        route3 = Route(
            title="Полный обзор центра",
            description="Расширенный маршрут по всем основным достопримечательностям центра Москвы. Для настоящих исследователей!",
            difficulty="hard",
            reward_xp=500.0,
            is_premium=True
        )
        db.add(route3)
        
        await db.flush()
        
        # 5. Associate POIs with Routes
        # Route 1: Красная площадь -> Храм Василия -> ГУМ -> Мавзолей
        await db.execute(route_poi_association.insert().values(route_id=route1.id, poi_id=pois[0].id, order=0))
        await db.execute(route_poi_association.insert().values(route_id=route1.id, poi_id=pois[1].id, order=1))
        await db.execute(route_poi_association.insert().values(route_id=route1.id, poi_id=pois[2].id, order=2))
        await db.execute(route_poi_association.insert().values(route_id=route1.id, poi_id=pois[3].id, order=3))
        
        # Route 2: Большой театр -> Третьяковка -> Арбат
        await db.execute(route_poi_association.insert().values(route_id=route2.id, poi_id=pois[5].id, order=0))
        await db.execute(route_poi_association.insert().values(route_id=route2.id, poi_id=pois[6].id, order=1))
        await db.execute(route_poi_association.insert().values(route_id=route2.id, poi_id=pois[7].id, order=2))
        
        # Route 3: All POIs
        for i, poi in enumerate(pois):
            await db.execute(route_poi_association.insert().values(route_id=route3.id, poi_id=poi.id, order=i))
        
        # 6. Create Quizzes (option_a, option_b, option_c, option_d, correct_answer="A"/"B"/"C"/"D")
        quizzes = [
            Quiz(
                poi_id=pois[0].id,
                question="В каком веке возникла Красная площадь?",
                option_a="XIV век",
                option_b="XV век",
                option_c="XVI век",
                option_d="XVII век",
                correct_answer="B",
                xp_reward=25.0
            ),
            Quiz(
                poi_id=pois[0].id,
                question="Как первоначально называлась Красная площадь?",
                option_a="Торг",
                option_b="Базар",
                option_c="Рынок",
                option_d="Ярмарка",
                correct_answer="A",
                xp_reward=25.0
            ),
            Quiz(
                poi_id=pois[1].id,
                question="По чьему приказу был построен храм Василия Блаженного?",
                option_a="Петр I",
                option_b="Иван Грозный",
                option_c="Екатерина II",
                option_d="Борис Годунов",
                correct_answer="B",
                xp_reward=25.0
            ),
            Quiz(
                poi_id=pois[1].id,
                question="В честь какого события был построен храм?",
                option_a="Победа над шведами",
                option_b="Взятие Казани",
                option_c="Освобождение от монголов",
                option_d="Коронация царя",
                correct_answer="B",
                xp_reward=25.0
            ),
            Quiz(
                poi_id=pois[2].id,
                question="В каком архитектурном стиле построен ГУМ?",
                option_a="Барокко",
                option_b="Классицизм",
                option_c="Псевдорусский",
                option_d="Модерн",
                correct_answer="C",
                xp_reward=25.0
            ),
            Quiz(
                poi_id=pois[5].id,
                question="В каком году был основан Большой театр?",
                option_a="1756",
                option_b="1776",
                option_c="1796",
                option_d="1816",
                correct_answer="B",
                xp_reward=25.0
            ),
            Quiz(
                poi_id=pois[6].id,
                question="Кто основал Третьяковскую галерею?",
                option_a="Павел Третьяков",
                option_b="Сергей Третьяков",
                option_c="Иван Третьяков",
                option_d="Николай Третьяков",
                correct_answer="A",
                xp_reward=25.0
            ),
            Quiz(
                poi_id=pois[7].id,
                question="С какого века известна улица Арбат?",
                option_a="XIV",
                option_b="XV",
                option_c="XVI",
                option_d="XVII",
                correct_answer="B",
                xp_reward=25.0
            ),
        ]
        
        for quiz in quizzes:
            db.add(quiz)
        
        await db.commit()
        print("✅ Seed data created successfully!")
        print("   Admin: admin@moscow.ru / admin123")
        print("   User: user@test.com / test123")
        print(f"   Routes: 3")
        print(f"   POIs: {len(pois)}")
        print(f"   Quizzes: {len(quizzes)}")

if __name__ == "__main__":
    asyncio.run(seed())
